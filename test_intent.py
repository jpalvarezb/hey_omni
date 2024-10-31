import asyncio
import logging
from omni.services.intent.engine import IntentEngine, Intent, IntentSlot

async def test_intent_engine():
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("Intent_Test")
    
    # Create and initialize engine
    engine = IntentEngine()
    
    try:
        # Test 1: Initialization
        logger.info("=== Test 1: Initialization ===")
        await engine.initialize()
        
        # Test 2: Weather Intents
        logger.info("=== Test 2: Weather Intents ===")
        weather_tests = [
            "What's the weather like?",
            "What's the weather in New York?",
            "What's the temperature tomorrow?",
            "Show me the forecast for tonight"
        ]
        
        for text in weather_tests:
            logger.info(f"\nTesting: '{text}'")
            result = await engine.process_text(text)
            if isinstance(result, dict):
                # Convert dict to Intent object
                slots = {
                    name: IntentSlot(name, data['value'], data['confidence'])
                    for name, data in result.get('slots', {}).items()
                }
                intent = Intent(
                    type=result['type'],
                    confidence=result['confidence'],
                    slots=slots,
                    raw_text=result.get('raw_text', text)
                )
            else:
                intent = result
                
            logger.info(f"Intent Type: {intent.type}")
            logger.info(f"Confidence: {intent.confidence:.2f}")
            logger.info("Slots:")
            for name, slot in intent.slots.items():
                logger.info(f"  {name}: {slot.value} (confidence: {slot.confidence:.2f})")
                
        # Test 3: Calendar Intents
        logger.info("\n=== Test 3: Calendar Intents ===")
        calendar_tests = [
            "What's on my calendar today?",
            "Add a meeting for tomorrow",
            "Show my schedule for next week",
            "Delete the event at 5:00"
        ]
        
        for text in calendar_tests:
            logger.info(f"\nTesting: '{text}'")
            result = await engine.process_text(text)
            if isinstance(result, dict):
                # Convert dict to Intent object
                slots = {
                    name: IntentSlot(name, data['value'], data['confidence'])
                    for name, data in result.get('slots', {}).items()
                }
                intent = Intent(
                    type=result['type'],
                    confidence=result['confidence'],
                    slots=slots,
                    raw_text=result.get('raw_text', text)
                )
            else:
                intent = result
                
            logger.info(f"Intent Type: {intent.type}")
            logger.info(f"Confidence: {intent.confidence:.2f}")
            logger.info("Slots:")
            for name, slot in intent.slots.items():
                logger.info(f"  {name}: {slot.value} (confidence: {slot.confidence:.2f})")
                
        # Test 4: Timer Intents
        logger.info("\n=== Test 4: Timer Intents ===")
        timer_tests = [
            "Set a timer for 5 minutes",
            "Start a timer",
            "Stop the timer",
            "Remind me in 2 hours"
        ]
        
        for text in timer_tests:
            logger.info(f"\nTesting: '{text}'")
            result = await engine.process_text(text)
            if isinstance(result, dict):
                # Convert dict to Intent object
                slots = {
                    name: IntentSlot(name, data['value'], data['confidence'])
                    for name, data in result.get('slots', {}).items()
                }
                intent = Intent(
                    type=result['type'],
                    confidence=result['confidence'],
                    slots=slots,
                    raw_text=result.get('raw_text', text)
                )
            else:
                intent = result
                
            logger.info(f"Intent Type: {intent.type}")
            logger.info(f"Confidence: {intent.confidence:.2f}")
            logger.info("Slots:")
            for name, slot in intent.slots.items():
                logger.info(f"  {name}: {slot.value} (confidence: {slot.confidence:.2f})")
                
        # Test 5: Unknown Intents
        logger.info("\n=== Test 5: Unknown Intents ===")
        unknown_tests = [
            "Hello there",
            "Play some music",
            "What's the meaning of life?"
        ]
        
        for text in unknown_tests:
            logger.info(f"\nTesting: '{text}'")
            result = await engine.process_text(text)
            if isinstance(result, dict):
                # Convert dict to Intent object
                slots = {
                    name: IntentSlot(name, data['value'], data['confidence'])
                    for name, data in result.get('slots', {}).items()
                }
                intent = Intent(
                    type=result['type'],
                    confidence=result['confidence'],
                    slots=slots,
                    raw_text=result.get('raw_text', text)
                )
            else:
                intent = result
                
            logger.info(f"Intent Type: {intent.type}")
            logger.info(f"Confidence: {intent.confidence:.2f}")
            
        logger.info("\nAll tests completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    finally:
        await engine.cleanup()

if __name__ == "__main__":
    asyncio.run(test_intent_engine()) 