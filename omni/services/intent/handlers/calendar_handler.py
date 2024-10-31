import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base import BaseIntentHandler
from ..engine import Intent, IntentSlot
import re
import dateparser

class CalendarHandler(BaseIntentHandler):
    """Handler for calendar-related intents."""
    
    # Calendar-specific patterns
    ACTIONS = {
        "view": ["show", "view", "check", "what", "list"],
        "add": ["add", "create", "new", "schedule"],
        "delete": ["delete", "remove", "cancel"],
        "update": ["update", "change", "modify", "edit"]
    }
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        
    async def can_handle(self, intent: Intent) -> bool:
        """Check if this handler can process the intent."""
        if intent.type != "calendar":
            return False
            
        # Check confidence and required slots
        has_action = any(
            word in intent.raw_text.lower()
            for action_words in self.ACTIONS.values()
            for word in action_words
        )
        
        return intent.confidence > 0.4 and has_action
        
    async def handle(self, intent: Intent) -> Dict[str, Any]:
        """Handle calendar intent."""
        try:
            # Determine action
            action = self._determine_action(intent.raw_text)
            
            # Get time from slots or use default
            time_slot = intent.slots.get("time", IntentSlot("time", "today", 1.0))
            
            # Handle different actions
            if action == "view":
                return await self._handle_view(time_slot.value)
            elif action == "add":
                return await self._handle_add(intent)
            elif action == "delete":
                return await self._handle_delete(intent)
            elif action == "update":
                return await self._handle_update(intent)
                
            return {
                "success": False,
                "error": "Unknown calendar action",
                "feedback": "I'm not sure what you want to do with your calendar."
            }
            
        except Exception as e:
            self._logger.error(f"Error handling calendar intent: {e}")
            return {
                "success": False,
                "error": str(e),
                "feedback": "Sorry, I couldn't process your calendar request."
            }
            
    def _determine_action(self, text: str) -> str:
        """Determine calendar action from text."""
        text = text.lower()
        for action, words in self.ACTIONS.items():
            if any(word in text for word in words):
                return action
        return "view"  # Default action
        
    async def _handle_view(self, time_value: str) -> Dict[str, Any]:
        """Handle viewing calendar events."""
        # TODO: Implement actual calendar viewing
        return {
            "success": True,
            "action": "view",
            "time": time_value,
            "events": [],  # Would contain actual events
            "feedback": f"You have no events scheduled for {time_value}."
        }
        
    async def _handle_add(self, intent: Intent) -> Dict[str, Any]:
        """Handle adding calendar events."""
        try:
            # Extract event details from intent
            event_name = None
            start_time = None
            duration = None
            
            # Check slots first
            if 'title' in intent.slots:
                event_name = intent.slots['title'].value
            if 'time' in intent.slots:
                start_time = intent.slots['time'].value
            if 'duration' in intent.slots:
                duration = self._parse_duration(intent.slots['duration'].value)
                
            # Try to extract from raw text if not in slots
            if not event_name:
                name_match = re.search(r"named\s+([a-zA-Z0-9\s]+?)(?:\s+to\s+|$)", intent.raw_text)
                if name_match:
                    event_name = name_match.group(1).strip()
                    self._logger.info(f"Found event name in command: {event_name}")
                    
            # If we don't have event name, need to ask
            if not event_name:
                return {
                    "success": False,
                    "action": "add",
                    "needs_info": "event_name",
                    "feedback": "What would you like to name the event?"
                }
                
            # If we don't have start time, need to ask
            if not start_time:
                return {
                    "success": False,
                    "action": "add",
                    "event_name": event_name,
                    "needs_info": "start_time",
                    "feedback": f"When would you like to schedule {event_name}?"
                }
                
            # If we don't have duration, need to ask
            if not duration:
                return {
                    "success": False,
                    "action": "add",
                    "event_name": event_name,
                    "start_time": start_time,
                    "needs_info": "duration",
                    "feedback": f"How long should {event_name} last?"
                }
                
            # Format duration for feedback
            duration_str = self._format_duration(timedelta(seconds=duration))
            
            # We have all needed information
            event_details = {
                "summary": event_name,
                "start": self._format_datetime(start_time),
                "end": self._format_datetime(self._add_duration(start_time, duration)),
                "duration": duration_str
            }
            
            # Return with confirmation request
            return {
                "success": True,
                "action": "add",
                "event_details": event_details,
                "needs_confirmation": True,
                "feedback": (
                    f"I'll create an event named '{event_name}' "
                    f"starting at {self._format_time(start_time)}, "
                    f"lasting {duration_str}. "
                    "Would you like to confirm this?"
                )
            }
            
        except Exception as e:
            self._logger.error(f"Error handling calendar add: {e}")
            return {
                "success": False,
                "action": "add",
                "error": str(e),
                "feedback": "Sorry, I couldn't create the event."
            }
            
    def _format_datetime(self, dt) -> Dict[str, str]:
        """Format datetime for calendar API."""
        if isinstance(dt, str):
            dt = self._parse_datetime(dt)
            
        return {
            'dateTime': dt.isoformat(),
            'timeZone': 'UTC'  # Or get from system/user preferences
        }
        
    def _format_time(self, time_value: Any) -> str:
        """Format time for display."""
        if isinstance(time_value, datetime):
            return time_value.strftime('%I:%M %p')
        return str(time_value)
        
    def _add_duration(self, start_time: Any, duration_seconds: int) -> datetime:
        """Add duration to start time."""
        if isinstance(start_time, str):
            start_time = self._parse_datetime(start_time)
            
        return start_time + timedelta(seconds=duration_seconds)
        
    def _parse_datetime(self, value: Any) -> datetime:
        """Parse various datetime formats."""
        if isinstance(value, datetime):
            return value
            
        if isinstance(value, dict):
            # Handle calendar API datetime format
            dt_str = value.get('dateTime', value.get('date'))
            if dt_str:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                
        # Parse string representations
        try:
            return dateparser.parse(str(value))
        except:
            raise ValueError(f"Could not parse datetime: {value}")
        
    async def _handle_delete(self, intent: Intent) -> Dict[str, Any]:
        """Handle deleting calendar events."""
        # TODO: Implement event deletion
        time_slot = intent.slots.get("time", IntentSlot("time", "today", 1.0))
        
        return {
            "success": True,
            "action": "delete",
            "time": time_slot.value,
            "feedback": f"Deleted event for {time_slot.value}."
        }
        
    async def _handle_update(self, intent: Intent) -> Dict[str, Any]:
        """Handle updating calendar events."""
        try:
            # Initialize update parameters
            update_params = {
                'new_name': None,
                'new_start_time': None,
                'new_duration': None,
                'new_summary': None
            }
            
            # Extract event name from intent
            event_name = None
            if 'title' in intent.slots:
                event_name = intent.slots['title'].value
            else:
                # Try to extract from raw text
                name_match = re.search(
                    r"named\s+([a-zA-Z0-9\s]+?)(?:\s+to\s+|$)", 
                    intent.raw_text
                )
                if name_match:
                    event_name = name_match.group(1).strip()
                    self._logger.info(f"Found event name in command: {event_name}")
                    
            # Extract duration if present
            if 'duration' in intent.slots:
                duration_str = intent.slots['duration'].value
                update_params['new_duration'] = self._parse_duration(duration_str)
                self._logger.info(f"Found duration in command: {duration_str}")
                
            # If no event name, we need to ask
            if not event_name:
                return {
                    "success": False,
                    "action": "update",
                    "needs_info": "event_name",
                    "feedback": "Which event would you like to update?"
                }
                
            # Find the event
            event = await self._find_event(event_name)
            if not event:
                return {
                    "success": False,
                    "action": "update",
                    "error": f"Could not find an event named '{event_name}'",
                    "feedback": f"I couldn't find an event named '{event_name}'"
                }
                
            # Get current event details
            current_start = self._parse_datetime(event['start'])
            current_end = self._parse_datetime(event['end'])
            current_duration = current_end - current_start
            
            # Format current duration for feedback
            duration_str = self._format_duration(current_duration)
            
            # If we have updates from intent
            if update_params['new_duration']:
                new_duration_str = self._format_duration(
                    timedelta(seconds=update_params['new_duration'])
                )
                
                return {
                    "success": True,
                    "action": "update",
                    "event_id": event['id'],
                    "updates": update_params,
                    "needs_confirmation": True,
                    "feedback": (
                        f"I'll update the event duration to {new_duration_str}. "
                        "Would you like to confirm this update?"
                    )
                }
                
            # If no specific updates provided, return options
            return {
                "success": True,
                "action": "update",
                "event_id": event['id'],
                "current_details": {
                    "title": event['summary'],
                    "start": current_start.strftime('%I:%M %p'),
                    "duration": duration_str
                },
                "update_options": [
                    "Event title",
                    "Start time",
                    "Duration",
                    "Event description"
                ],
                "feedback": (
                    f"Current event details: {event['summary']}, "
                    f"starting at {current_start.strftime('%I:%M %p')}, "
                    f"duration: {duration_str}. "
                    "You may update: Event title, Start time, Duration, or Event description."
                )
            }
            
        except Exception as e:
            self._logger.error(f"Error handling calendar update: {e}")
            return {
                "success": False,
                "action": "update",
                "error": str(e),
                "feedback": "Sorry, I couldn't update the event."
            }
            
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string into seconds."""
        number_map = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        try:
            parts = duration_str.lower().split()
            number = parts[0]
            unit = parts[1].rstrip('s')  # Remove plural 's'
            
            # Convert word numbers to digits
            if number in number_map:
                number = number_map[number]
            else:
                number = int(number)
                
            # Convert to seconds
            multiplier = {
                'minute': 60,
                'hour': 3600,
                'day': 86400
            }.get(unit, 60)  # Default to minutes
            
            return number * multiplier
            
        except Exception as e:
            self._logger.error(f"Error parsing duration: {e}")
            return None
            
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display."""
        total_minutes = int(duration.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        parts = []
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            
        return " and ".join(parts)
        
    async def get_help(self) -> str:
        """Get help for calendar commands."""
        return (
            "Calendar commands:\n"
            "- 'What's on my calendar?' to view events\n"
            "- 'Add event' to create new event\n"
            "- 'Delete event' to remove event\n"
            "- 'Update event' to modify existing event"
        ) 