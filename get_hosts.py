from swimlane.core.search import EQ
from swimlane import Swimlane
import pendulum
import requests
import json
requests.packages.urllib3.disable_warnings()


def main():
  
  # Vectra Instance Variable
  instance_name = 'Vectra'
  
  #Swimlane vairables
  swimlane = Swimlane(sw_context.config['InternalSwimlaneUrl'], access_token=sw_context.inputs['swimlane_api_pat'], verify_ssl=False)
  vectra_app = swimlane.apps.get(name='CDC - Vectra')
  
  # Key Store vairables
  vectra_url = sw_context.inputs['vectra_url'] 
  token = sw_context.inputs['vectra_token']
  
  # API endpoint
  hosts_url = f'https://{vectra_url}/api/v2.5/hosts'
  
  headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {token}'
  }

  # Filters data for hosts with a State of "active" and a threat score greater than 50, and sorts by last_detection_timestamp
  params = {
    'page_size': 100,
    'state': 'active',
    't_score_gte': 50,
    'c_score_gte':50,  #Remove this to get high alerts
    'ordering': 'last_detection_timestamp',
  }
  
  # Makes api call to Vectra
  response = get_hosts(hosts_url, headers, params)
  
  if response:
    host_data = response.json()['results']
    
    if host_data:
      for host in host_data:
      
        vectra_id = host['id']
        old_id = check_existing_records_for_vectra_id(vectra_id, vectra_app)
      
        if not old_id:
          field_data = get_field_data(host, instance_name)
          print(field_data)
          create_record(vectra_app, field_data)
      else:
        print('***NO RECORD CREATED - OLD ID***')
    else:
      print('***REQUEST RETURNED NONE***')    
    

# Makes API call to Vectra
def get_hosts(hosts_url, headers, params, timeout=60):
  
  try:
    response = requests.get(hosts_url, headers=headers, params=params, timeout=timeout, verify=False)
    
    if response.status_code ==  200:
      return response
    else:
      print(f'Request failed - {response.status_code} - {response.headers}')
      
  except requests.exceptions.Timeout:
    print(f'Request timed out after {timeout} seconds')    
  except requests.exceptions.RequestException as e:
    print(f'Error: {e}')
    
  return None


# Returns current time
def get_current_time():
  return pendulum.now('America/Denver')


# Convert date_time string to a datetime object
def parse_datetime(date_string):
  return pendulum.parse(date_string)


# Checks existing records for vectra hosts id and return True if a record exists with that id, otherwise returns False
def check_existing_records_for_vectra_id(vectra_id, vectra_app):
  
  # This records search returns a list with the record_id(s) if the vectra_id already exists in a record, otherwise it returns an empty list
  records = vectra_app.records.search(
    ('Vectra Id', EQ, vectra_id)
    )
  
  return True if records else False


def get_field_data(host, instance_name):
  
  current_time = get_current_time()
    
  field_data = {
    'Record Created At': current_time,
    'Vectra Instance' : instance_name,
  }
  
  # Vectra Id
  try:
    field_data['Vectra Id'] = host.get('id', None)
  except Exception as e:
    print(f'DEBUG - Vectra Id Error: {e}')
    pass
  # Vectra Name
  try:
    field_data['Vectra Name'] = host.get('name', None)
  except Exception as e:
    print(f'DEBUG - Vectra Name Error: {e}')
    pass
  # Vectra IP
  try:
    field_data['Vectra IP'] = host.get('ip', None)
  except Exception as e:
    print(f'DEBUG - Vectra IP Error: {e}')
    pass
  # Vectra Severity
  try:
    field_data['Vectra Severity'] = host.get('severity', None)
  except Exception as e:
    print(f'DEBUG - Vectra Severity Error: {e}')
    pass
  # Vectra Threat Score
  try:
    field_data['Vectra Threat Score'] = host.get('t_score', None)
  except Exception as e:
    print(f'DEBUG - Vectra Threat Score Error: {e}')
    pass
  # Vectra Certainty Score
  try:
    field_data['Vectra Certainty Score'] = host.get('c_score', None)
  except Exception as e:
    print(f'DEBUG - Vectra Certainty Score Error: {e}')
    pass
  # Vectra Last Detection (MDT) and Vectra Last Detection (UTC)
  try:
    date_string = host.get('last_detection_timestamp', None)
    if date_string:
      datetime_mdt = parse_datetime(date_string)
      field_data['Vectra Last Detection (MDT)'] = datetime_mdt
  except Exception as e:
    print(f'DEBUG - Vectra Last Detection Error: {e}')
    pass
  # Vectra Tags
  try:
    vectra_tags = host.get('tags', [])
    if vectra_tags:
      field_data['Vectra Tags'] = vectra_tags
  except Exception as e:
    print(f'DEBUG - Vectra Tags Error: {e}')
    pass
  # Vectra Groups 
  try:
    vectra_groups = host.get('groups', [])
    group_names = [group['name'] for group in vectra_groups]
    if vectra_groups:
      field_data['Vectra Groups'] = group_names
  except Exception as e:
    print(f'DEBUG - Vectra Groups Error: {e}')
    pass
  # Vectra Sensor
  try:
    field_data['Vectra Sensor'] = host.get('sensor', None)
  except Exception as e:
    print(f'DEBUG - Vectra Sensor Error: {e}')
    pass
  # Vectra Sensor Name
  try:
    field_data['Vectra Sensor Name'] = host.get('sensor_name', None)
  except Exception as e:
    print(f'DEBUG - Vectra Sensor Error: {e}')
    pass
  
  return field_data


# Creates Vectra Record
def create_record(vectra_app, field_data):
  
  new_record = vectra_app.records.create(**field_data)


# Calls "main" function  
if __name__ == '__main__':
  main()