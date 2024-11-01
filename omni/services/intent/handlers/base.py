"""Base intent handler."""
from abc import ABC, abstractmethod
from typing import Optional
import logging
from ....models.intent import Intent, IntentResult, IntentFeedback, IntentType
from ....core.exceptions import IntentError

class BaseIntentHandler(ABC):
    """Base class for intent handlers."""
    
    def __init__(self):
        """Initialize base handler."""
        self._logger = logging.getLogger(self.__class__.__name__)
        
    async def handle(self, intent: Intent) -> IntentResult:
        """Handle intent.
        
        Args:
            intent: Intent to handle
            
        Returns:
            IntentResult: Result of handling intent
        """
        try:
            # Validate intent
            if not isinstance(intent, Intent):
                self._logger.warning("Invalid intent type provided")
                return self._create_error_result(
                    error=IntentError("Invalid intent type"),
                    intent_type=IntentType.UNKNOWN,
                    custom_text="I couldn't understand your request.",
                    custom_speech="Sorry, I didn't get that."
                )
                
            # Check if handler can process
            try:
                if not await self.can_handle(intent):
                    self._logger.warning(f"Handler cannot process intent type: {intent.type}")
                    return self._create_error_result(
                        error=IntentError(f"Cannot process intent type: {intent.type}"),
                        intent_type=intent.type,
                        custom_text="I can't handle that type of request.",
                        custom_speech="Sorry, I can't help with that."
                    )
            except Exception as e:
                self._logger.error(f"Error in can_handle: {e}")
                return self._create_error_result(
                    error=e,
                    intent_type=intent.type,
                    custom_text="I had trouble processing your request.",
                    custom_speech="Sorry, something went wrong."
                )
                
            # Process intent
            return await self._process_intent(intent)
            
        except IntentError as e:
            self._logger.warning(f"Intent processing error: {e}")
            return self._create_error_result(
                error=e,
                intent_type=getattr(intent, 'type', IntentType.UNKNOWN),
                custom_text=str(e),
                custom_speech="Sorry, I couldn't process your request."
            )
            
        except Exception as e:
            self._logger.error(f"Unexpected error in handle: {e}", exc_info=True)
            return self._create_error_result(
                error=e,
                intent_type=getattr(intent, 'type', IntentType.UNKNOWN),
                custom_text="An unexpected error occurred.",
                custom_speech="Sorry, something went wrong."
            )
            
    @abstractmethod
    async def can_handle(self, intent: Intent) -> bool:
        """Check if handler can process intent.
        
        Args:
            intent: Intent to check
            
        Returns:
            bool: True if handler can process intent
            
        Raises:
            IntentError: If intent validation fails
        """
        raise NotImplementedError
        
    @abstractmethod
    async def _process_intent(self, intent: Intent) -> IntentResult:
        """Process the intent after validation.
        
        Args:
            intent: Validated intent to process
            
        Returns:
            IntentResult: Result of processing intent
            
        Raises:
            IntentError: If processing fails
        """
        raise NotImplementedError
        
    @abstractmethod
    async def get_help(self) -> str:
        """Get help text for handler.
        
        Returns:
            str: Help text describing handler capabilities
        """
        raise NotImplementedError
        
    def _create_error_result(
        self,
        error: Exception,
        intent_type: IntentType = IntentType.UNKNOWN,
        needs_followup: bool = False,
        followup_type: Optional[str] = None,
        custom_text: Optional[str] = None,
        custom_speech: Optional[str] = None,
        custom_display: Optional[dict] = None
    ) -> IntentResult:
        """Create error result with consistent formatting.
        
        Args:
            error: Exception that occurred
            intent_type: Type of intent that failed
            needs_followup: Whether followup is needed
            followup_type: Type of followup needed
            custom_text: Optional custom error message
            custom_speech: Optional custom speech message
            custom_display: Optional custom display data
            
        Returns:
            IntentResult: Formatted error result
        """
        return IntentResult(
            success=False,
            feedback=IntentFeedback(
                text=custom_text or str(error),
                speech=custom_speech or "Sorry, there was a problem.",
                display=custom_display
            ),
            type=intent_type,
            error=str(error),
            needs_followup=needs_followup,
            followup_type=followup_type,
            slots={}
        )