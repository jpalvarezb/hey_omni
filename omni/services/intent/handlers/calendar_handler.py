"""Calendar intent handler."""
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from .base import BaseIntentHandler
from ....models.intent import Intent, IntentResult, IntentFeedback, IntentType, IntentSlot
from ....core.exceptions import CalendarError, AuthError, IntentError
from ...cloud.api.calendar_service import CalendarAPI

class CalendarHandler(BaseIntentHandler):
    """Handler for calendar intents."""
    
    # Calendar-specific patterns
    ACTIONS = {
        "view": ["show", "view", "check", "what", "list", "see"],
        "add": ["add", "create", "new", "schedule", "set"],
        "delete": ["delete", "remove", "cancel", "clear"],
        "update": ["update", "change", "modify", "edit", "reschedule"]
    }
    
    # Required slots per action
    REQUIRED_SLOTS = {
        "view": ["time"],
        "add": ["time", "title"],
        "delete": ["time", "title"],
        "update": ["time", "title"]
    }
    
    def __init__(self, calendar_api: CalendarAPI):
        """Initialize calendar handler."""
        super().__init__()
        self._api = calendar_api
        
    async def can_handle(self, intent: Intent) -> bool:
        """Check if handler can process intent."""
        # Determine action and required slots
        action = self._determine_action(intent.raw_text)
        if not action:
            return False
            
        # Validate required slots for action
        required_slots = self.REQUIRED_SLOTS.get(action, [])
        has_valid_slots = all(
            slot in intent.slots and 
            isinstance(intent.slots[slot], IntentSlot)
            for slot in required_slots
        )
        
        return (
            intent.type == IntentType.CALENDAR and 
            intent.confidence > 0.5 and 
            has_valid_slots
        )
        
    async def _process_intent(self, intent: Intent) -> IntentResult:
        """Process calendar intent."""
        try:
            # Determine action
            action = self._determine_action(intent.raw_text)
            if not action:
                self._logger.warning("Unknown calendar action requested")
                return self._create_error_result(
                    error=IntentError("Unknown calendar action"),
                    intent_type=intent.type,
                    custom_text="I'm not sure what you want to do with your calendar.",
                    custom_speech="I don't understand what calendar action you want.",
                    custom_display={'error_type': 'unknown_action'}
                )
                
            # Validate required slots
            missing_slots = self._check_required_slots(intent, action)
            if missing_slots:
                self._logger.warning(f"Missing required slots for {action}: {missing_slots}")
                return self._create_error_result(
                    error=IntentError(f"Missing required slots: {', '.join(missing_slots)}"),
                    intent_type=intent.type,
                    needs_followup=True,
                    followup_type=missing_slots[0],
                    custom_text=self._get_slot_prompt(missing_slots[0]),
                    custom_speech=self._get_slot_prompt(missing_slots[0], is_speech=True)
                )
                
            # Handle action
            try:
                if action == "view":
                    return await self._handle_view(intent)
                elif action == "add":
                    return await self._handle_add(intent)
                elif action == "delete":
                    return await self._handle_delete(intent)
                elif action == "update":
                    return await self._handle_update(intent)
                    
            except AuthError as e:
                self._logger.error(f"Calendar authentication failed: {e}")
                return self._create_error_result(
                    error=e,
                    intent_type=intent.type,
                    custom_text="Sorry, I'm having trouble accessing your calendar. Please check your authentication.",
                    custom_speech="I can't access your calendar right now.",
                    custom_display={'error_type': 'auth_error'}
                )
                
            except CalendarError as e:
                self._logger.error(f"Calendar API failed: {e}")
                return self._create_error_result(
                    error=e,
                    intent_type=intent.type,
                    custom_text=f"Sorry, I couldn't access your calendar: {str(e)}",
                    custom_speech="Sorry, I had trouble with your calendar request.",
                    custom_display={'error_type': 'api_error'}
                )
                
        except Exception as e:
            self._logger.error(f"Unexpected error in calendar handler: {e}", exc_info=True)
            return self._create_error_result(
                error=e,
                intent_type=intent.type,
                custom_text="Sorry, something went wrong while accessing your calendar.",
                custom_speech="Sorry, I encountered an error with your calendar request."
            )
            
    def _determine_action(self, text: str) -> Optional[str]:
        """Determine calendar action from text."""
        text = text.lower()
        for action, words in self.ACTIONS.items():
            if any(word in text for word in words):
                return action
        return None
        
    def _check_required_slots(self, intent: Intent, action: str) -> list:
        """Check for required slots based on action."""
        required_slots = self.REQUIRED_SLOTS.get(action, [])
        return [
            slot for slot in required_slots
            if slot not in intent.slots or not isinstance(intent.slots[slot], IntentSlot)
        ]
        
    def _get_slot_prompt(self, slot: str, is_speech: bool = False) -> str:
        """Get prompt for missing slot."""
        prompts = {
            "time": (
                "When would you like to check your calendar?",
                "What time would you like to check?"
            ),
            "title": (
                "What's the title of the event?",
                "What should I call this event?"
            )
        }
        return prompts.get(slot, ("Please provide more information.", "I need more information."))[1 if is_speech else 0]
        
    async def _handle_view(self, intent: Intent) -> IntentResult:
        """Handle view action."""
        time_slot = intent.slots['time']
        events = await self._api.list_events(
            start_time=time_slot.value.isoformat(),
            end_time=(time_slot.value + timedelta(days=1)).isoformat()
        )
        return self._format_view_response(events, intent.type)
        
    async def _handle_add(self, intent: Intent) -> IntentResult:
        """Handle add action."""
        # Not implemented yet
        return self._create_error_result(
            error=IntentError("Add action not implemented"),
            intent_type=intent.type,
            custom_text="Sorry, I can't add events to your calendar yet.",
            custom_speech="I can't add calendar events yet."
        )
        
    async def _handle_delete(self, intent: Intent) -> IntentResult:
        """Handle delete action."""
        # Not implemented yet
        return self._create_error_result(
            error=IntentError("Delete action not implemented"),
            intent_type=intent.type,
            custom_text="Sorry, I can't delete events from your calendar yet.",
            custom_speech="I can't delete calendar events yet."
        )
        
    async def _handle_update(self, intent: Intent) -> IntentResult:
        """Handle update action."""
        # Not implemented yet
        return self._create_error_result(
            error=IntentError("Update action not implemented"),
            intent_type=intent.type,
            custom_text="Sorry, I can't update calendar events yet.",
            custom_speech="I can't update calendar events yet."
        )
        
    def _format_view_response(self, events: list, intent_type: IntentType) -> IntentResult:
        """Format view response."""
        if not events:
            return IntentResult(
                success=True,
                feedback=IntentFeedback(
                    text="You have no events scheduled.",
                    speech="Your calendar is clear.",
                    display={'type': 'calendar_empty'}
                ),
                data={'events': []},
                type=intent_type
            )
            
        formatted_events = [
            {
                'title': event['summary'],
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date'))
            }
            for event in events
        ]
        
        return IntentResult(
            success=True,
            feedback=IntentFeedback(
                text=self._format_events_text(formatted_events),
                speech=self._format_events_speech(formatted_events),
                display={
                    'type': 'calendar_events',
                    'events': formatted_events
                }
            ),
            data={'events': formatted_events},
            type=intent_type
        )
        
    def _format_events_text(self, events: list) -> str:
        """Format events for text display."""
        lines = ["Here are your events:"]
        for event in events:
            start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
            lines.append(f"- {event['title']} at {start.strftime('%I:%M %p')}")
        return "\n".join(lines)
        
    def _format_events_speech(self, events: list) -> str:
        """Format events for speech."""
        if len(events) == 1:
            event = events[0]
            start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
            return f"You have {event['title']} at {start.strftime('%I:%M %p')}"
        return f"You have {len(events)} events scheduled."
        
    async def get_help(self) -> str:
        """Get help text."""
        return (
            "I can help you with your calendar. Try:\n"
            "- What's on my calendar today?\n"
            "- Add a meeting tomorrow at 2pm\n"
            "- Show my events for next week\n"
            "- Delete the meeting at 3pm"
        )