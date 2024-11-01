"""Tests for utility functions."""
import pytest
from datetime import datetime, timedelta
import logging
from omni.utils.main import parse_time, parse_location, normalize_text, remove_filter_words
from omni.models.intent import Location
from omni.core.exceptions import ParserError

@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests."""
    logging.basicConfig(level=logging.DEBUG)

def test_remove_filter_words():
    """Test removing filter words."""
    assert remove_filter_words("weather in London") == "in London"
    assert remove_filter_words("what's the temperature") == ""
    assert remove_filter_words("") == ""
    assert remove_filter_words("London") == "London"

def test_normalize_text():
    """Test text normalization."""
    assert normalize_text("What's the Weather?") == "whats the weather"
    assert normalize_text("It's   HOT!!!") == "its hot"
    assert normalize_text("") == ""
    assert normalize_text("London, UK") == "london uk"

@pytest.mark.parametrize("input_text, expected", [
    # Basic city tests
    ("weather in London", Location(city="London")),
    ("what's the weather like in New York", Location(city="New York")),
    ("Paris forecast", Location(city="Paris")),
    
    # Tests with state
    ("Miami, FL weather", Location(city="Miami", state="FL")),
    ("temperature in Seattle, WA", Location(city="Seattle", state="WA")),
    
    # Tests with country
    ("weather in Paris, France", Location(city="Paris", country="France")),
    
    # Tests with noise words
    ("what's the hourly forecast for Tokyo tomorrow", Location(city="Tokyo")),
    ("will it rain next week in London", Location(city="London")),
    
    # Edge cases
    ("", None),
    ("what's the weather like", None),
    ("show me the forecast", None),
])
def test_parse_location(input_text, expected):
    """Test location parsing."""
    result = parse_location(input_text)
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result.city == expected.city
        if expected.state:
            assert result.state == expected.state
        if expected.country:
            assert result.country == expected.country

def test_parse_location_invalid_input():
    """Test invalid input raises ParserError."""
    with pytest.raises(ParserError):
        parse_location(None)
    with pytest.raises(ParserError):
        parse_location(123)

def test_specific_times():
    """Test parsing specific times."""
    result = parse_time("midnight")
    assert result['datetime'].hour == 0
    assert result['datetime'].minute == 0
    
    result = parse_time("noon")
    assert result['datetime'].hour == 12
    assert result['datetime'].minute == 0

def test_relative_times():
    """Test parsing relative times."""
    result = parse_time("in 30 minutes")
    assert result is not None
    
    # Get current time without microseconds for comparison
    now = datetime.now().replace(microsecond=0)
    expected = now + timedelta(minutes=30)
    result_time = result['datetime'].replace(microsecond=0)
    
    # Compare times within 1 second tolerance
    assert abs((result_time - expected).total_seconds()) <= 1

def test_specific_time_formats():
    """Test specific time formats."""
    result = parse_time("3:30pm")
    assert result['datetime'].hour == 15
    assert result['datetime'].minute == 30
    
    result = parse_time("9am")
    assert result['datetime'].hour == 9
    assert result['datetime'].minute == 0

def test_error_handling():
    """Test error handling in time parsing."""
    with pytest.raises(ParserError):
        parse_time(None)