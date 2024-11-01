from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Response:
    """Standard response model."""
    success: bool
    message: str
    type: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> 'Response':
        """Create response from data dictionary."""
        try:
            # Determine response type
            response_type = 'unknown'
            if 'error' in data:
                response_type = 'error'
            elif 'weather' in data:
                response_type = 'weather'
            elif 'calendar' in data:
                response_type = 'calendar'
            elif 'text' in data:
                response_type = 'text'
                
            return cls(
                success=True,
                message=data.get('text', ''),
                type=response_type,
                data=data,
                error=data.get('error')
            )
            
        except Exception as e:
            return cls(
                success=False,
                message=str(e),
                type='error',
                error=str(e)
            )
