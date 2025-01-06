from swimlane import Swimlane
import requests
requests.packages.urllib3.disable_warnings()
import re


def main():
  
  #Swimlane variables
  swimlane = Swimlane(sw_context.config['InternalSwimlaneUrl'], access_token=sw_context.inputs['swimlane_api_pat'], verify_ssl=False)
  alert_management_app = swimlane.apps.get(name="Alert & Incident Management")
  saim_record = alert_management_app.records.get(id=sw_context.config['RecordId'])
  
  # SAIM variables
  user = str(saim_record['case_current-owner'])
  instance_name = saim_record['Vectra Instance']
  vectra_host_id = saim_record['Vectra Id']
  
  # Authentication variables
  token = get_vectra_token(instance_name)
  url = get_vectra_url(instance_name)
  
  # URL variables
  users_url = f'{url}/api/v2.5/users'
  assignment_url = f'{url}/api/v2.5/assignments'
  
  headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {token}'
  }
  
  
  if user != 'None' and user != None:
    name = format_user(user)
    
    params = {
    'username': name, 
    }
    
    
    # Calls vectra_request function to {url}/api/v2.5/users
    user_id = vectra_request(users_url, headers, params, request_type=1)
    
    if user_id:
       
      vectra_user_id = get_user_id(user_id)
      
      json_data = {
        'assign_host_id': vectra_host_id,
        'assign_to_user_id': vectra_user_id,
      }
      
      #Calls vectra_request function to {url}/api/v2.5/assignments
      assignment = vectra_request(assignment_url, headers, json_data, request_type=2)
      #assignment = None
      if assignment:
        
        vectra_assignment_id = get_assignment_id(assignment)
        
        if vectra_assignment_id:
          update_saim_record(saim_record, vectra_user_id, vectra_assignment_id)
  
  
# Returns vectra_token based on instance
def get_vectra_token(instance_name):
  if instance_name == 'Vectra01':
    return sw_context.inputs['vectra01_token']
  elif instance_name == 'Vectra02':
    return sw_context.inputs['vectra02_token']
  else:
    return sw_context.inputs['vectra03_token']
  
  
# Returns vectra_url based on instance
def get_vectra_url(instance_name):
  if instance_name == 'Vectra01':
    return sw_context.inputs['vectra01_url']
  elif instance_name == 'Vectra02':
    return sw_context.inputs['vectra02_url']
  else:
    return sw_context.inputs['vectra03_url']
  

# Returns a user string "SAML:P0123456" from the swimlane case_current_owner
def format_user(name):
  pattern = r'\((P\d+)\)'
  match = re.search(pattern, name)
  return f'SAML:{match.group(1)}'


# Returns a sting of the vectra_user_id
def get_user_id(user_id):
  user_id = user_id.json()['results'][0]
  return user_id.get('id', None)


# Returns a vectra assignment id that would be needed to re-assign or delete a user from a host in vectra
def get_assignment_id(assignment):
  assignment = assignment.json()['assignment']
  return assignment.get('id', None)


# Makes API call to Vectra
def vectra_request(url, headers, data, request_type, timeout=60):
  
  try:
    if request_type == 1:
      
      # API call to {url}/api/v2.5/users, to get the vectra_id for the user that correspondes to the swimlane user who claimed the SAIM ticket
      response = requests.get(url, headers=headers, params=data, timeout=timeout, verify=False)
      
      if response.status_code ==  200:
        return response
      else:
        print(f'Request failed - {response.status_code} - {response.headers}')
    
    else:
      
      # API call to {url}/api/v2.5/assignments, to assign the host in vectra to the user who claimed the SAIM ticket
      response = requests.post(url, headers=headers, json=data, timeout=timeout, verify=False)
      
      if response.status_code ==  201:
        return response
      else:
        print(f'Request failed - {response.status_code} - {response.headers}')
      
  except requests.exceptions.Timeout:
    print(f'Request timed out after {timeout} seconds')    
  except requests.exceptions.RequestException as e:
    print(f'Error: {e}')
    
  return None
 
  
# Updates the SAIM Record with the Vectra User Id and Vectra Assignment Id - These fields are always hidden in Alert & Incident Management
# These ids are needed if you want to update or delete the user assigned to the host in vectra
def update_saim_record(saim_record, vectra_user_id, vectra_assignment_id):
  
  saim_record['Vectra User Id'] = vectra_user_id
  saim_record['Vectra Assignment Id'] = vectra_assignment_id
  saim_record.patch()  
  

# Calls main function  
if __name__ == '__main__':
  main()