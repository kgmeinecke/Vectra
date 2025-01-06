from swimlane import Swimlane


def main():

  # Define communications tracker app and current app objects 
  swimlane = Swimlane(sw_context.config['InternalSwimlaneUrl'], access_token=sw_context.inputs['swimlane_api_pat'], verify_ssl=False)
  vectra_app = swimlane.apps.get(id=sw_context.config['ApplicationId'])
  vectra_record = vectra_app.records.get(id=sw_context.config['RecordId'])
  communications_app = swimlane.apps.get(name="Communications Tracker")

  
  # Create SCT data
  sct_data = create_sct_data(vectra_record)
  
  # Create SCT Record
  new_sct_record = create_sct_record(communications_app, sct_data)
  
  # Update SCT Record
  update_sct_record(new_sct_record)
  
  # Update Vectra Record
  update_vectra_record(vectra_record, new_sct_record)
  
  
# Creates a dictionary of data to write to the SCT record  
def create_sct_data(vectra_record):  

  # Create variable for Subject
  vectra_alert_id = vectra_record['Vectra Id']
  vectra_alert_name = vectra_record['Vectra Name']

  sct_data = {
    'Subject': f'Vectra - {vectra_alert_id} - {vectra_alert_name}'
  }

  return sct_data


# Created new Communications Record
def create_sct_record(communications_app, sct_data):
  new_sct_record = communications_app.records.create(**sct_data)
  
  return new_sct_record


# Update Communications Record
def update_sct_record(new_sct_record):
  new_sct_record['Communications Record Id'] = new_sct_record.id
  new_sct_record.patch()

  
# Update Vectra Record
def update_vectra_record(vectra_record, new_sct_record):

  vectra_record['Record Id'] = vectra_record
  vectra_record['Communications Record Id'] = new_sct_record.id
  vectra_record['Communications Tracking Id'] = new_sct_record.tracking_id
  vectra_record['Communications Tracker'].add(new_sct_record)
  vectra_record.patch()


if __name__ == '__main__':
  main()