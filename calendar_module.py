import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone

# SCOPES for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Authenticate with Google Calendar
def authenticate_google_calendar():
    """Authenticates the user with Google Calendar and returns a service object."""
    creds = None
    token_path = 'token.pickle'
    
    # Check if token.pickle exists to load credentials
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate using OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('calendar', 'v3', credentials=creds)
    return service

# Add event to Google Calendar
def add_event(service, summary, start_time, end_time):
    """Adds a new event to the user's calendar."""
    try:
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'America/Mexico_City'},
            'end': {'dateTime': end_time, 'timeZone': 'America/Mexico_City'}
        }
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event '{summary}' created with ID: {created_event.get('id')}")
        return f"Event '{summary}' created."
    except Exception as e:
        print(f"An error occurred while adding the event: {e}")
        return "Failed to create the event."

# List upcoming events
def list_upcoming_events(service):
    """Lists the next 10 events on the user's calendar."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        if not events:
            print('No upcoming events found.')
            return "No upcoming events."
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            print(f"{start} - {summary}")
            event_list.append(f"{start} - {summary}")
        
        return event_list
    except Exception as e:
        print(f"An error occurred while listing events: {e}")
        return "Failed to retrieve events."

# Update an existing event
def update_event(service, event_id, updated_summary=None, updated_start_time=None, updated_end_time=None):
    """Updates an existing event in the user's calendar."""
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        if updated_summary:
            event['summary'] = updated_summary
        if updated_start_time:
            event['start']['dateTime'] = updated_start_time
        if updated_end_time:
            event['end']['dateTime'] = updated_end_time

        updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
        print(f"Event '{updated_event.get('summary')}' updated.")
        return f"Event '{updated_event.get('summary')}' updated."
    except Exception as e:
        print(f"An error occurred while updating the event: {e}")
        return "Failed to update the event."

# Delete an event from Google Calendar with user-friendly response
def delete_event(service, event_id):
    """Deletes an event from the user's calendar."""
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        event_title = event.get('summary', 'Unnamed Event')
        event_start = event['start'].get('dateTime', event['start'].get('date'))
        event_time = datetime.fromisoformat(event_start).strftime('%I:%M %p')
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        
        # Return a more user-friendly response with event details
        return f"Event '{event_title}' scheduled at {event_time} canceled."
    except Exception as e:
        print(f"An error occurred while deleting the event: {e}")
        return f"Failed to delete the event."

# Utility to retrieve event by title
def find_event_by_title(service, title):
    """Finds an event by its title."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        for event in events:
            if event.get('summary', '').lower() == title.lower():
                return event
        
        return None
    except Exception as e:
        print(f"An error occurred while searching for the event: {e}")
        return None

# Main function for testing the Google Calendar integration
def main():
    service = authenticate_google_calendar()

    # Example: Listing events
    events = list_upcoming_events(service)
    if events:
        print("Upcoming events:")
        for event in events:
            print(event)

    # Example: Adding an event
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
    end_time = (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat() + 'Z'
    add_event(service, 'New Test Event', start_time, end_time)

    # Example: Updating an event
    event_id = 'ENTER_YOUR_EVENT_ID_HERE'
    update_event(service, event_id, updated_summary='Updated Event Title')

    # Example: Deleting an event
    delete_event(service, event_id)

if __name__ == '__main__':
    main()