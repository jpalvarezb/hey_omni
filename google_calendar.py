import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """Shows basic usage of the Google Calendar API.
    Returns a service object to interact with the Google Calendar API."""
    
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('calendar', 'v3', credentials=creds)
    return service

def list_upcoming_events(service):
    """Lists the next 10 events on the user's calendar."""
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start} - {event['summary']}")
        print(f"Event ID: {event['id']}")  # Print event ID to update/delete

def add_event(service, summary, start_time, end_time):
    """Adds a new event to the user's calendar."""
    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/Mexico_City',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/Mexico_City',
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"Event created: {event.get('htmlLink')}")

def update_event(service, event_id, updated_summary=None, updated_start_time=None, updated_end_time=None):
    """Updates an existing event on the user's calendar."""
    event = service.events().get(calendarId='primary', eventId=event_id).execute()

    if updated_summary:
        event['summary'] = updated_summary
    if updated_start_time:
        event['start']['dateTime'] = updated_start_time
    if updated_end_time:
        event['end']['dateTime'] = updated_end_time

    updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
    print(f"Event updated: {updated_event.get('htmlLink')}")

def delete_event(service, event_id):
    """Deletes an event from the user's calendar."""
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"Event with ID {event_id} deleted successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    service = authenticate_google_calendar()

    # List events
    list_upcoming_events(service)

    # Add an event (example)
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
    end_time = (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat() + 'Z'
    add_event(service, 'New Test Event', start_time, end_time)

    # Update an event (use an event ID from listing events)
    # event_id = 'ENTER_YOUR_EVENT_ID_HERE'
    # update_event(service, event_id, 'Updated Test Event')

    # Delete an event (use an event ID from listing events)
    # event_id = 'ENTER_YOUR_EVENT_ID_HERE'
    # delete_event(service, event_id)

if __name__ == '__main__':
    main()