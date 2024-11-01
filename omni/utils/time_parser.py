"""Time parsing utilities."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re
import logging
from ..core.exceptions import TimeParserError, ParserError, ValidationError

logger = logging.getLogger(__name__)

class TimeParser:
    """Time parsing functionality."""
    
    # Time parsing patterns
    SPECIFIC_TIMES = {
        'midnight': (0, 0),
        'noon': (12, 0),
        'evening': (18, 0),
        'morning': (9, 0),
        'afternoon': (14, 0),
        'end of day': (23, 59)
    }
    
    RELATIVE_DAYS = {
        'day after tomorrow': 2,
        'tomorrow': 1,
        'next week': 7
    }
    
    WEEKDAYS = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }

    @classmethod
    def parse(cls, text: str) -> Optional[Dict[str, Any]]:
        """Parse time expressions from text."""
        try:
            if not text:
                return None
                
            now = datetime.now().replace(second=0, microsecond=0)
            result = {'datetime': now}
            
            # Handle specific times
            for phrase, (hour, minute) in cls.SPECIFIC_TIMES.items():
                if phrase in text.lower():
                    result['datetime'] = result['datetime'].replace(hour=hour, minute=minute)
                    return result
                    
            # Handle relative days
            for phrase, days in cls.RELATIVE_DAYS.items():
                if phrase in text.lower():
                    result['datetime'] = now + timedelta(days=days)
                    
            # Handle "next month"
            if 'next month' in text.lower():
                try:
                    if now.month == 12:
                        result['datetime'] = now.replace(year=now.year + 1, month=1)
                    else:
                        result['datetime'] = now.replace(month=now.month + 1)
                except ValueError:
                    # Handle edge cases (e.g., Jan 31 -> Feb 28)
                    next_month = now.month + 1 if now.month < 12 else 1
                    next_year = now.year + (1 if now.month == 12 else 0)
                    last_day = (datetime(next_year, next_month + 1, 1) - timedelta(days=1)).day
                    result['datetime'] = now.replace(year=next_year, month=next_month, day=min(now.day, last_day))
                    
            # Handle weekdays
            for day_name, target_weekday in cls.WEEKDAYS.items():
                if f'next {day_name}' in text.lower():
                    current_weekday = now.weekday()
                    days_ahead = (target_weekday - current_weekday + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7  # Next week if same day
                    result['datetime'] = now + timedelta(days=days_ahead)
                    
            # Handle relative minutes
            minutes_match = re.search(r'\bin (\d+) minutes?\b', text.lower())
            if minutes_match:
                minutes = int(minutes_match.group(1))
                result['datetime'] = now + timedelta(minutes=minutes)
                return result
                
            # Handle "in an hour"
            if 'in an hour' in text.lower():
                result['datetime'] = now + timedelta(hours=1)
                return result
                
            # Handle specific time mentions
            time_match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', text.lower())
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                if time_match.group(3) == 'pm' and hour < 12:
                    hour += 12
                elif time_match.group(3) == 'am' and hour == 12:
                    hour = 0
                result['datetime'] = result['datetime'].replace(hour=hour, minute=minute)
                
            return result
            
        except Exception as e:
            logger.error(f"Time parsing error: {e}")
            raise ParserError(f"Failed to parse time: {str(e)}") 