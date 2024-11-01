import os
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ....core.exceptions import APIError
from ....core.config import Config
import pickle

class CalendarAPI:
    """Google Calendar API client with async support."""
    
    BASE_URL = 'https://www.googleapis.com/calendar/v3'
    
    def __init__(self, config: Config):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        self._credentials = None
        self._config = config
        
    async def initialize(self) -> None:
        """Initialize calendar API client."""
        try:
            self._credentials = await self._get_credentials()
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self._credentials.token}"}
            )
            self._logger.info("Calendar API client initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize calendar API: {e}")
            raise APIError(f"Calendar API initialization failed: {str(e)}")
            
    async def _get_credentials(self) -> Credentials:
        """Get or refresh Google Calendar credentials."""
        try:
            creds = None
            calendar_config = self._config.calendar
            
            # Try to load from pickle file
            if os.path.exists(calendar_config.token_path):
                with open(calendar_config.token_path, 'rb') as token:
                    creds = pickle.load(token)
                    
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(calendar_config.credentials_path):
                        raise APIError("Calendar credentials not found")
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        calendar_config.credentials_path,
                        calendar_config.scopes
                    )
                    creds = flow.run_local_server(port=0)
                    
                # Save the credentials as pickle
                with open(calendar_config.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                    
            return creds
            
        except Exception as e:
            self._logger.error(f"Failed to get/refresh credentials: {e}")
            raise APIError(f"Authentication failed: {str(e)}")
            
    async def list_events(self, 
                         time_min: Optional[datetime] = None,
                         time_max: Optional[datetime] = None,
                         max_results: int = 10) -> List[Dict[str, Any]]:
        """List calendar events."""
        try:
            if not time_min:
                time_min = datetime.utcnow()
            if not time_max:
                time_max = time_min + timedelta(days=7)
                
            params = {
                'calendarId': 'primary',
                'timeMin': time_min.isoformat() + 'Z',
                'timeMax': time_max.isoformat() + 'Z',
                'maxResults': max_results,
                'singleEvents': 'true',
                'orderBy': 'startTime'
            }
            
            async with self._session.get(
                f"{self.BASE_URL}/calendars/primary/events",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                else:
                    text = await response.text()
                    raise APIError(f"Calendar API error: {text}")
                    
        except Exception as e:
            self._logger.error(f"Failed to list events: {e}")
            raise APIError(f"Failed to list calendar events: {str(e)}")
            
    async def create_event(self, event_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event."""
        try:
            async with self._session.post(
                f"{self.BASE_URL}/calendars/primary/events",
                json=event_details
            ) as response:
                if response.status == 200:
                    event = await response.json()
                    self._logger.info(f"Created event: {event.get('summary')}")
                    return event
                else:
                    text = await response.text()
                    raise APIError(f"Calendar API error: {text}")
                    
        except Exception as e:
            self._logger.error(f"Failed to create event: {e}")
            raise APIError(f"Failed to create calendar event: {str(e)}")
            
    async def update_event(self, 
                          event_id: str, 
                          updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a calendar event."""
        try:
            # Get current event
            async with self._session.get(
                f"{self.BASE_URL}/calendars/primary/events/{event_id}"
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise APIError(f"Failed to get event: {text}")
                event = await response.json()
                
            # Apply updates
            event.update(updates)
            
            # Update event
            async with self._session.put(
                f"{self.BASE_URL}/calendars/primary/events/{event_id}",
                json=event
            ) as response:
                if response.status == 200:
                    updated_event = await response.json()
                    self._logger.info(f"Updated event: {updated_event.get('summary')}")
                    return updated_event
                else:
                    text = await response.text()
                    raise APIError(f"Calendar API error: {text}")
                    
        except Exception as e:
            self._logger.error(f"Failed to update event: {e}")
            raise APIError(f"Failed to update calendar event: {str(e)}")
            
    async def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event."""
        try:
            async with self._session.delete(
                f"{self.BASE_URL}/calendars/primary/events/{event_id}"
            ) as response:
                if response.status in (200, 204):
                    self._logger.info(f"Deleted event: {event_id}")
                    return True
                else:
                    text = await response.text()
                    raise APIError(f"Calendar API error: {text}")
                    
        except Exception as e:
            self._logger.error(f"Failed to delete event: {e}")
            raise APIError(f"Failed to delete calendar event: {str(e)}")
            
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._session:
            await self._session.close() 