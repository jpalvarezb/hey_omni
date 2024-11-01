import pytest
from omni.utils.main import parse_location
from omni.models.intent import Location
from omni.core.exceptions import ParserError

@pytest.mark.parametrize("input_text, expected", [
    # Basic city tests
    ("weather in London", Location(city="London", confidence=1.0)),
    ("what's the weather like in New York", Location(city="New York", confidence=1.0)),
    ("Paris forecast", Location(city="Paris", confidence=1.0)),
    
    # Tests with state
    ("Miami, FL weather", Location(city="Miami", state="FL", confidence=1.0)),
    ("temperature in Seattle, WA", Location(city="Seattle", state="WA", confidence=1.0)),
    
    # Tests with noise words
    ("what's the hourly forecast for Tokyo tomorrow", Location(city="Tokyo", confidence=1.0)),
    ("will it rain next week in London", Location(city="London", confidence=1.0)),
    
    # Edge cases
    ("", None),
    ("what's the weather like", None),
    ("show me the forecast", None),
])
def test_parse_location(input_text, expected):
    result = parse_location(input_text)
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result.city == expected.city
        assert result.state == expected.state
        assert result.confidence == expected.confidence

def test_parse_location_invalid_input():
    """Test invalid input raises ParserError."""
    with pytest.raises(ParserError):
        parse_location(123)  # Pass non-string input