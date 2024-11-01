"""Main utility functions."""
from typing import Optional, Dict, Any, Set
from datetime import datetime, timedelta
import re
import logging
from ..models.intent import Location
from ..core.exceptions import (
    ParserError,
    TimeParserError,
    LocationParserError,
    ValidationError
)
from ..core.config import Config

# Constants
FILTER_WORDS: Set[str] = {
    'weather', 'forecast', 'temperature', 'climate', 
    'like', 'show', 'me', 'the', 'what', 'whats', 
    'will', 'it', 'rain', 'next', 'week', 'tomorrow', 
    'tonight', 'hourly', 'daily'
}

QUESTION_WORDS: Set[str] = {
    'what', 'how', 'when', 'where', 'why', 'who'
}

PREPOSITIONS: Set[str] = {'in', 'at', 'for', 'near', 'by'}

TIME_PATTERNS: Dict[str, Any] = {
    'specific': {
        'midnight': (0, 0),
        'noon': (12, 0),
        'evening': (18, 0),
        'morning': (9, 0),
        'afternoon': (14, 0),
        'end of day': (23, 59)
    },
    'relative_days': {
        'day after tomorrow': 2,
        'tomorrow': 1,
        'next week': 7
    }
}

logger = logging.getLogger(__name__)

def remove_filter_words(text: str) -> str:
    """Remove filter words from text.
    
    Args:
        text: Text to clean
        
    Returns:
        str: Text with filter words removed
    """
    if not text:
        return ""
        
    # Keep original case
    words = text.split()
    # Don't filter out contractions like "what's"
    filtered_words = [word for word in words if word.lower().replace("'s", "") not in FILTER_WORDS]
    return ' '.join(filtered_words)

def normalize_text(text: str) -> str:
    """Normalize input text."""
    if not text:
        return ""
        
    logger.debug(f"Normalizing text: '{text}'")
    
    # Convert to lowercase
    text = text.lower()
    logger.debug(f"After lowercase: '{text}'")
    
    # Handle contractions
    text = text.replace("'s", "s")
    text = text.replace("'t", "t")
    text = text.replace("'re", "re")
    text = text.replace("'ve", "ve")
    text = text.replace("'m", "m")
    text = text.replace("'ll", "ll")
    text = text.replace("'d", "d")
    logger.debug(f"After contraction handling: '{text}'")
    
    # Remove extra whitespace and special characters
    text = ' '.join(text.split())
    text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text)
    text = ' '.join(text.split())
    
    result = text.strip()
    logger.debug(f"Final normalized text: '{result}'")
    return result

def _clean_city_name(city: str) -> str:
    """Clean city name by removing prepositions and extra spaces."""
    if not city:
        return ""
        
    logger.debug(f"Cleaning city name: '{city}'")
    
    # Remove leading/trailing spaces
    city = city.strip()
    
    # Remove leading prepositions
    words = city.split()
    if words and words[0].lower() in PREPOSITIONS:
        logger.debug(f"Removing leading preposition '{words[0]}'")
        words = words[1:]
        
    # Join and clean
    city = ' '.join(words).strip().title()
    logger.debug(f"Cleaned city name: '{city}'")
    return city

def parse_location(text: str, should_remove_filter_words: bool = True) -> Optional[Location]:
    """Parse location from text."""
    try:
        logger.debug(f"Parsing location from: '{text}'")
        
        # Input validation
        if not isinstance(text, str):
            logger.warning("Invalid input type for location parsing")
            raise ParserError("Input must be a string")
        if not text.strip():
            logger.debug("Empty text, returning None")
            return None
            
        # Clean text if requested
        cleaned_text = remove_filter_words(text) if should_remove_filter_words else text
        logger.debug(f"Cleaned text: '{cleaned_text}'")
        
        # Skip if only contains filter words
        if not cleaned_text.strip():
            logger.debug("Text only contained filter words")
            return None
            
        # Try city, state pattern first
        state_match = re.search(r'([A-Za-z\s]+?),\s*([A-Z]{2})\b', cleaned_text)
        if state_match:
            city = _clean_city_name(state_match.group(1))
            state = state_match.group(2)
            logger.debug(f"Found city, state pattern: {city}, {state}")
            return Location(city=city, state=state)
            
        # Try city, country pattern
        country_match = re.search(r'([A-Za-z\s]+?),\s*([A-Za-z]+)\b', cleaned_text)
        if country_match:
            city = _clean_city_name(country_match.group(1))
            country = country_match.group(2)
            if len(country) == 2:
                logger.debug(f"Found city, state code pattern: {city}, {country}")
                return Location(city=city, state=country.upper())
            logger.debug(f"Found city, country pattern: {city}, {country}")
            return Location(city=city, country=country)
            
        # Try preposition pattern
        prep_match = re.search(
            r'\b(?:in|at|for)\s+([A-Za-z\s]+(?:\s+[A-Za-z]+)*?)\b(?:,|\s|$)',
            cleaned_text
        )
        if prep_match:
            city = _clean_city_name(prep_match.group(1))
            if city and not any(word in city.lower() for word in FILTER_WORDS):
                logger.debug(f"Found preposition pattern: {city}")
                return Location(city=city)
                
        # Try direct city mention
        direct_match = re.search(
            r'^([A-Za-z\s]+(?:\s+[A-Za-z]+)*?)\b(?:,|\s|$)',
            cleaned_text
        )
        if direct_match:
            city = _clean_city_name(direct_match.group(1))
            if city and not any(word in city.lower() for word in FILTER_WORDS):
                logger.debug(f"Found direct city mention: {city}")
                return Location(city=city)
                
        logger.debug("No location pattern matched")
        return None
        
    except Exception as e:
        logger.warning(f"Location parsing error: {e}")
        raise ParserError(f"Failed to parse location: {str(e)}")

def parse_time(text: str) -> Optional[Dict[str, Any]]:
    """Parse time expressions from text."""
    try:
        if not text:
            return None
            
        now = datetime.now().replace(second=0, microsecond=0)
        result = {'datetime': now}
        
        # Handle relative minutes
        minutes_match = re.search(r'in (\d+) minutes?\b', text.lower())
        if minutes_match:
            minutes = int(minutes_match.group(1))
            result['datetime'] = now + timedelta(minutes=minutes)
            return result
            
        # Handle specific times
        for phrase, (hour, minute) in TIME_PATTERNS['specific'].items():
            if phrase in text.lower():
                logger.debug(f"Found specific time pattern: {phrase}")
                result['datetime'] = result['datetime'].replace(hour=hour, minute=minute)
                return result
                
        # Handle relative days
        for phrase, days in TIME_PATTERNS['relative_days'].items():
            if phrase in text.lower():
                logger.debug(f"Found relative day pattern: {phrase}")
                result['datetime'] = now + timedelta(days=days)
                
        # Handle specific time mentions
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', text.lower())
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3)
            
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
                
            logger.debug(f"Found specific time mention: {hour}:{minute:02d}")
            result['datetime'] = result['datetime'].replace(hour=hour, minute=minute)
            
        return result
        
    except Exception as e:
        logger.warning(f"Time parsing error: {e}")
        raise ParserError(f"Failed to parse time: {str(e)}")
