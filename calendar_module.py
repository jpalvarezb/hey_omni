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
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service

# Add event to Google Calendar
def add_event(service, summary, start_time, end_time):
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
        print(f"An error occurred: {e}")
        return "Failed to create the event."

# List upcoming events
def list_upcoming_events(service):
    now = datetime.now(timezone.utc).isoformat()
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

# Update an existing event
def update_event(service, event_id, updated_summary=None, updated_start_time=None, updated_end_time=None):
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    if updated_summary:
        event['summary'] = updated_summary
    if updated_start_time:
        event['start']['dateTime'] = updated_start_time
    if updated_end_time:
        event['end']['dateTime'] = updated_end_time
    updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
    return f"Event '{updated_summary}' updated."

# Delete an event from Google Calendar
def delete_event(service, event_id):
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return f"Event with ID {event_id} deleted successfully."
    except Exception as e:
        return f"Error occurred: {e}"