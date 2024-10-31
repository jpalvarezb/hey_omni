import asyncio
import logging
from omni.services.speech.synthesis.local_tts import LocalTTSEngine

async def test_tts():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("TTS_Test")
    
    tts = LocalTTSEngine()
    
    try:
        # Test 1: Initialization
        logger.info("=== Test 1: Initialization ===")
        await tts.initialize({
            'rate': 150,
            'volume': 1.0
        })
        
        # Test 2: Basic speech using _speak_with_timeout
        logger.info("=== Test 2: Basic speech ===")
        logger.info("Speaking: 'Hello, this is a test'")
        await tts._speak_with_timeout("Hello, this is a test", timeout=5.0)
        await asyncio.sleep(1)  # Brief pause
        
        # Test 3: Short sentences
        logger.info("=== Test 3: Short sentences ===")
        sentences = [
            "Testing one.",
            "Testing two.",
            "Testing three."
        ]
        
        for sentence in sentences:
            logger.info(f"Speaking: {sentence}")
            await tts._speak_with_timeout(sentence, timeout=3.0)
            await asyncio.sleep(0.5)  # Brief pause between sentences
            
        logger.info("Tests completed!")
        
    except asyncio.CancelledError:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
    finally:
        logger.info("Cleaning up...")
        await tts.cleanup()
        logger.info("Cleanup complete")

if __name__ == "__main__":
    try:
        asyncio.run(test_tts())
    except KeyboardInterrupt:
        print("\nTest stopped by user")