from swimlane import Swimlane
import pendulum
from swimlane.core.resources.usergroup import UserGroup


def main():
  
  # Swimlane App and Record Variables
  swimlane = Swimlane(sw_context.config['InternalSwimlaneUrl'], access_token=sw_context.inputs['swimlane_api_pat'], verify_ssl=False)
  
  vectra_app = swimlane.apps.get(name='CDC - Vectra')
  vectra_record = vectra_app.records.get(id=sw_context.config['RecordId'])
  
  alert_management_app = swimlane.apps.get(name="Alert & Incident Management")
  
  communications_app = swimlane.apps.get(name='Communications Tracker')
  sct_record = communications_app.records.get(id=vectra_record['Communications Record Id'])
  
  # Create SAIM Data
  saim_data = create_saim_data(vectra_record, sct_record, swimlane)
  
  # Create SAIM Record
  saim_record = create_saim_record(alert_management_app, saim_data)
  print('***Record Created***')
  
  # Update Xpanse Record
  update_vectra_record(vectra_record, saim_record)
  
  # Update SCT Record
  update_sct_record(sct_record, saim_record)
  
  # Update SAIM Record
  update_saim_record(saim_record, sct_record)
  

# Returns current time
def get_current_time():
  return pendulum.now('America/Denver')


# Returns current time minus 1 minute
def update_time(time):
  return time.subtract(minutes=1)


# Returns vectra_url based on instance
def get_url(instance):
  return sw_context.inputs['vectra02_url'] if instance == 'Vectra02' else(sw_context.inputs['vectra03_url'] if instance == 'Vectra03' else sw_context.inputs['vectra01_url'])


# Creates a dictionary of data to write to the SAIM record
def create_saim_data(vectra_record, sct_record, swimlane):
  
  instance = vectra_record['Vectra Instance']
  vectra_url = get_url(instance)
  
  title = vectra_record['Vectra Name']
  host_id = vectra_record['Vectra Id']
  vectra_url = f'https://{vectra_url}/hosts?search=host.id%3A%22{host_id}%22'
  now = get_current_time()
  min_ago = update_time(now)
  
  saim_data = {
    
    # Xpanse Fields
    'Vectra Name': title,
    'Vectra Id': host_id,
    'Vectra IP': vectra_record['Vectra IP'],
    'Vectra Instance': instance,
    'Vectra Severity': vectra_record['Vectra Severity'],
    'Vectra Threat Score': vectra_record['Vectra Threat Score'],
    'Vectra Certainty Score': vectra_record['Vectra Certainty Score'],
    'Vectra Last Detection (MDT)': vectra_record['Vectra Last Detection (MDT)'],
    'Vectra Tags': list(vectra_record['Vectra Tags']),
    'Vectra Groups': list(vectra_record['Vectra Groups']),
    
    # SAIM Fields
    
    #'Case Status': 'New',
    'Case Status': 'Open',
    'Case Classification / Resolution': 'Unknown',
    #'Case Current Owner': None,
    'Case Current Owner': swimlane.user,
    'Case Title': f'Vectra: {title}',
    'Detailed Summary': f'<a href="{vectra_url}" target="_blank">Vectra - {title}</a>',
    'Case Severity': vectra_record['Vectra Severity'].capitalize(),
    'Case Category': 'Unauthorized Access',
    'Case Source / Type': 'Vectra',
    'SCT-ID': sct_record,
    'Source Record Id': sw_context.config['RecordId'],
    'Source Application Id': sw_context.config['ApplicationId'],
    # Fields needed for Metrics
    'Event Occurred On': min_ago,
    'Alert Received On': now,
  }

  return saim_data


# Creates Alert & Incident Management Record
def create_saim_record(alert_management_app, saim_data):
  
  saim_record = alert_management_app.records.create(**saim_data)
  
  return saim_record


# Updates Vectra Record with time the SAIM Case is created
def update_vectra_record(vectra_record, saim_record):
  
  vectra_record['SAIM Case Created On'] = get_current_time()
  vectra_record['SAIM Tracking Id'] = saim_record.tracking_id
  vectra_record['SAIM Reference'].add(saim_record)
  vectra_record.patch()

  
# Updates the Communications Record with the SAIM ID  
def update_sct_record(sct_record, saim_record):
  
  sct_record['Incident Tracking Id'] = saim_record
  sct_record.patch()
  

# Updates the SAIM Reference Sections with the Communications Tracker Record
def update_saim_record(saim_record, sct_record):
  
  saim_record['Communications Tracker'].add(sct_record)
  saim_record.patch()
  
                            
# Calls main function
if __name__ == '__main__':
  main()