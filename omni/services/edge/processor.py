import asyncio
import logging
import uuid
import heapq
import time
from typing import Optional, Dict, Any, Union, List, Tuple
from enum import Enum, auto
from dataclasses import dataclass
from collections import deque, defaultdict
from .cache.memory_cache import MemoryCache
from ...core.exceptions import EdgeProcessingError, ResourceInitializationError
from ..speech.synthesis.local_tts import LocalTTSEngine
from ..speech.synthesis.base import BaseSynthesizer
from ..speech.wake_word.porcupine import PorcupineWakeWord
from ..speech.wake_word.base import BaseWakeWordDetector
from ..speech.recognition.vosk import VoskRecognizer
from ..speech.recognition.base import BaseRecognizer
import os

class TaskConnectivity(Enum):
    """Task connectivity requirements with fallback behavior."""
    OFFLINE = "offline"
    ONLINE = "online"
    HYBRID = "hybrid"

class TaskType(Enum):
    """Types of tasks that can be processed locally."""
    WEATHER = "weather"
    CALENDAR = "calendar"
    TIMER = "timer"
    DEVICE_CONTROL = "device_control"

class PriorityLevel(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class RetryConfig:
    """Retry configuration by priority level."""
    MAX_RETRIES = {
        PriorityLevel.CRITICAL: 5,
        PriorityLevel.HIGH: 3,
        PriorityLevel.MEDIUM: 2,
        PriorityLevel.LOW: 1,
    }
    BASE_DELAY = {
        PriorityLevel.CRITICAL: 0.1,
        PriorityLevel.HIGH: 0.5,
        PriorityLevel.MEDIUM: 1.0,
        PriorityLevel.LOW: 2.0,
    }

class BatchMetrics:
    """Tracks batch processing performance."""
    def __init__(self):
        self.total_time = 0.0
        self.batch_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()
        
    @property
    def average_time(self) -> float:
        """Calculate average batch processing time."""
        return self.total_time / max(1, self.batch_count)
        
    @property
    def success_rate(self) -> float:
        """Calculate batch success rate."""
        total = self.success_count + self.failure_count
        return self.success_count / max(1, total)

class BatchConfig:
    """Configuration for task batching."""
    MAX_BATCH_SIZE = 10
    BATCH_WINDOW = 5.0  # seconds
    BATCHABLE_TYPES = {
        TaskType.WEATHER,  # Weather updates can be batched
        TaskType.CALENDAR  # Calendar checks can be batched
    }

class CachePolicy:
    """Defines caching behavior for different connectivity states."""
    def __init__(self, 
                 online_ttl: Optional[int] = 3600,    # 1 hour
                 offline_ttl: Optional[int] = None,   # No expiry when offline
                 max_age: Optional[int] = 86400):     # 24 hours max
        self.online_ttl = online_ttl
        self.offline_ttl = offline_ttl
        self.max_age = max_age

class FeedbackPriority(Enum):
    """Priority levels for voice feedback."""
    CRITICAL = 0    # Emergency/safety messages
    HIGH = 1        # Important task feedback
    NORMAL = 2      # Regular task feedback
    LOW = 3         # Informational messages

class FeedbackCategory(Enum):
    """Categories of voice feedback."""
    SYSTEM = auto()
    ERROR = auto()
    TASK = auto()
    GUIDE = auto()
    STATUS = auto()

@dataclass
class FeedbackConfig:
    """Configuration for voice feedback."""
    enabled: bool = True
    volume: float = 1.0
    silent_mode: bool = False
    delay_between_messages: float = 0.5
    allow_interruptions: bool = True
    haptic_enabled: bool = True
    guide_enabled: bool = True
    status_updates_enabled: bool = True

class FeedbackMessage:
    """Enhanced feedback message with metadata."""
    def __init__(self, 
                 text: str,
                 category: FeedbackCategory,
                 priority: FeedbackPriority = FeedbackPriority.NORMAL,
                 task_type: Optional[TaskType] = None,
                 interruptible: bool = True):
        self.text = text
        self.category = category
        self.priority = priority
        self.task_type = task_type
        self.timestamp = time.time()
        self.interruptible = interruptible

class ListeningState(Enum):
    """States for the listening cycle."""
    IDLE = "idle"                 # Waiting for wake word
    WAKE_WORD_DETECTED = "wake"   # Wake word detected
    LISTENING = "listening"       # Actively listening for command
    PROCESSING = "processing"     # Processing command
    ERROR = "error"              # Error state

class EdgeProcessor:
    """Handles edge computing tasks with continuous listening."""
    
    PRIORITY_MAP = {
        TaskType.DEVICE_CONTROL: PriorityLevel.HIGH,
        TaskType.TIMER: PriorityLevel.HIGH,
        TaskType.CALENDAR: PriorityLevel.MEDIUM,
        TaskType.WEATHER: PriorityLevel.LOW,
    }
    
    # Initial timeouts (seconds)
    BASE_TIMEOUTS = {
        PriorityLevel.CRITICAL: 2,
        PriorityLevel.HIGH: 5,
        PriorityLevel.MEDIUM: 10,
        PriorityLevel.LOW: 30,
    }
    
    # Monitoring thresholds
    ERROR_THRESHOLD = 0.1
    TIMEOUT_THRESHOLD = 0.1
    QUEUE_THRESHOLD = 100
    
    # Task connectivity requirements
    CONNECTIVITY_MAP = {
        TaskType.WEATHER: TaskConnectivity.ONLINE,      # Requires API access
        TaskType.CALENDAR: TaskConnectivity.HYBRID,     # Can work offline with local data
        TaskType.TIMER: TaskConnectivity.OFFLINE,       # Fully offline capable
        TaskType.DEVICE_CONTROL: TaskConnectivity.OFFLINE  # Local control
    }
    
    # Offline fallback messages
    OFFLINE_MESSAGES = {
        TaskType.WEATHER: "Weather updates require internet connection. Using cached data if available.",
        TaskType.CALENDAR: "Calendar sync unavailable offline. Showing local calendar data.",
    }
    
    # Cache policies for different task types
    CACHE_POLICIES = {
        TaskType.WEATHER: CachePolicy(
            online_ttl=1800,     # 30 minutes online
            offline_ttl=None,     # Don't expire offline
            max_age=43200        # 12 hours maximum age
        ),
        TaskType.CALENDAR: CachePolicy(
            online_ttl=3600,     # 1 hour online
            offline_ttl=None,     # Don't expire offline
            max_age=86400        # 24 hours maximum age
        )
    }
    
    # Offline capabilities for hybrid tasks
    OFFLINE_CAPABILITIES = {
        TaskType.CALENDAR: {
            'online': ['full_sync', 'create_event', 'modify_event'],
            'offline': ['view_events', 'create_local_event']
        },
        TaskType.WEATHER: {
            'online': ['current_weather', 'forecast', 'alerts'],
            'offline': ['cached_weather', 'last_known_forecast']
        }
    }
    
    # Feedback configuration
    FEEDBACK_DELAY = 0.5  # seconds between non-priority messages
    MAX_QUEUE_SIZE = 10   # maximum pending messages
    
    # Enhanced voice messages dictionary
    VOICE_MESSAGES = {
        'system': {
            'offline': {
                'text': "I'm currently offline. Some features may be limited.",
                'priority': FeedbackPriority.HIGH,
                'category': FeedbackCategory.SYSTEM
            },
            'low_battery': {
                'text': "Battery is low. Please charge soon.",
                'priority': FeedbackPriority.HIGH,
                'category': FeedbackCategory.STATUS
            },
            'storage_warning': {
                'text': "Storage space is running low.",
                'priority': FeedbackPriority.NORMAL,
                'category': FeedbackCategory.STATUS
            },
            'shutting_down': {
                'text': "Shutting down.",
                'priority': FeedbackPriority.HIGH,
                'category': FeedbackCategory.SYSTEM
            },
            'processing': {
                'text': "Processing your request.",
                'priority': FeedbackPriority.NORMAL,
                'category': FeedbackCategory.SYSTEM
            }
        },
        'error': {
            'network': {
                'text': "Network connection lost. Switching to offline mode.",
                'priority': FeedbackPriority.HIGH,
                'category': FeedbackCategory.ERROR
            },
            'task_failed': {
                'text': "Task couldn't be completed. Would you like to try again?",
                'priority': FeedbackPriority.NORMAL,
                'category': FeedbackCategory.GUIDE
            }
        },
        TaskType.WEATHER.value: {
            'cached': "Here's the latest weather information I have.",
            'updating': "Updating weather information.",
            'error': "Unable to fetch weather updates.",
        },
        TaskType.CALENDAR.value: {
            'offline': "Showing your local calendar events.",
            'syncing': "Syncing your calendar.",
            'event_added': "Event added to calendar.",
        },
        TaskType.TIMER.value: {
            'started': "Timer started.",
            'cancelled': "Timer cancelled.",
            'completed': "Timer complete!",
        },
        TaskType.DEVICE_CONTROL.value: {
            'success': "Device control successful.",
            'error': "Device control failed.",
        }
    }
    
    # Listening configuration
    LISTEN_TIMEOUT = 5.0  # seconds to listen after wake word
    MAX_SILENCE = 2.0     # seconds of silence before stopping listen
    
    def __init__(self, 
                 cache_size: int = 1000, 
                 cache_cleanup_interval: int = 3600,
                 offline_mode: bool = False,
                 feedback_config: Optional[FeedbackConfig] = None,
                 audio_buffer_size: int = 2048,
                 retry_delay: float = 0.5,
                 max_retries: int = 3,
                 startup_delay: float = 0.5):
        self._cache = MemoryCache(
            max_size=cache_size,
            cleanup_interval=cache_cleanup_interval
        )
        self._running = False
        self._lock = asyncio.Lock()
        self._offline_mode = offline_mode
        self._feedback_config = feedback_config or FeedbackConfig()
        
        # Platform-specific settings
        self._audio_buffer_size = audio_buffer_size
        self._retry_delay = retry_delay
        self._max_retries = max_retries
        self._startup_delay = startup_delay
        
        self._task_queue: List[Tuple[int, int, asyncio.Task]] = []
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._active_timers: Dict[str, asyncio.Task] = {}
        self._logger = logging.getLogger(self.__class__.__name__)
        self._task_counter = 0
        self._stats = self._initialize_stats()
        self._performance_metrics = defaultdict(dict)
        self._last_health_check = time.time()
        self._adaptive_timeouts = self.BASE_TIMEOUTS.copy()
        self._batch_queues = {
            task_type: [] for task_type in BatchConfig.BATCHABLE_TYPES
        }
        self._batch_timers: Dict[TaskType, Optional[asyncio.Task]] = {
            task_type: None for task_type in BatchConfig.BATCHABLE_TYPES
        }
        self._batch_configs = {
            TaskType.WEATHER: BatchConfig(),
            TaskType.CALENDAR: BatchConfig()
        }
        self._batch_metrics = {
            task_type: BatchMetrics() 
            for task_type in self._batch_configs
        }
        self._connectivity_status = not offline_mode
        self._tts_engine: Optional[BaseSynthesizer] = None
        self._voice_feedback_enabled = True
        self._feedback_queue: deque = deque(maxlen=self.MAX_QUEUE_SIZE)
        self._feedback_task: Optional[asyncio.Task] = None
        self._last_feedback_time = 0
        self._current_feedback: Optional[FeedbackMessage] = None
        self._feedback_lock = asyncio.Lock()
        self._wake_word_detector: Optional[BaseWakeWordDetector] = None
        self._speech_recognizer: Optional[BaseRecognizer] = None
        self._listening_state = ListeningState.IDLE
        self._listening_task: Optional[asyncio.Task] = None
        self._last_audio_time = 0
        
        # Add model paths
        self._vosk_model_path = "./vosk-model-small-en-us-0.15"
        
    async def start(self) -> None:
        """Start the processor and begin listening."""
        if not self._running:
            try:
                # Initialize all components
                await self.initialize()
                
                # Indicate ready state
                await self._queue_feedback(
                    "Ready and listening",
                    FeedbackCategory.SYSTEM,
                    FeedbackPriority.HIGH
                )
                
                self._logger.info("EdgeProcessor started and listening for wake word")
                
            except Exception as e:
                self._logger.error(f"Failed to start processor: {str(e)}")
                raise
                
    async def initialize(self) -> None:
        """Initialize processor components."""
        try:
            # Initialize TTS
            self._tts_engine = LocalTTSEngine()
            await self._tts_engine.initialize()
            
            # Initialize wake word detector
            self._wake_word_detector = PorcupineWakeWord()
            await self._wake_word_detector.initialize()
            
            # Initialize speech recognizer with correct model path
            self._speech_recognizer = VoskRecognizer(self._vosk_model_path)
            await self._speech_recognizer.initialize()
            
            # Start other components
            await self._cache.start()
            self._running = True
            
            # Start continuous listening loop
            self._listening_task = asyncio.create_task(self._listening_loop())
            
        except Exception as e:
            self._logger.error(f"Initialization failed: {str(e)}")
            raise ResourceInitializationError(f"Failed to initialize: {str(e)}")
                
    async def _listening_loop(self) -> None:
        """Main listening loop with state management."""
        try:
            # Start wake word detection once
            await self._wake_word_detector.start_detection()
            
            while self._running:
                try:
                    if self._listening_state == ListeningState.IDLE:
                        detected = await self._wake_word_detector.detect()
                        if detected:
                            self._logger.info("Wake word detected!")
                            await self._transition_to_listening()
                            
                    elif self._listening_state == ListeningState.LISTENING:
                        await self._process_audio_input()
                        
                    elif self._listening_state == ListeningState.ERROR:
                        await self._reset_listening_state()
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._logger.error(f"Error in listening loop: {str(e)}")
                    self._listening_state = ListeningState.ERROR
                    await asyncio.sleep(1)
                    
        finally:
            # Clean up
            if self._wake_word_detector:
                await self._wake_word_detector.stop_detection()
            if self._speech_recognizer:
                await self._speech_recognizer.stop_recognition()
        
    async def _transition_to_listening(self) -> None:
        """Transition to active listening state."""
        try:
            self._listening_state = ListeningState.WAKE_WORD_DETECTED
            
            # Stop wake word detection first
            await self._wake_word_detector.stop_detection()
            
            # Acknowledge wake word
            await self._queue_feedback(
                "Yes?",
                FeedbackCategory.SYSTEM,
                FeedbackPriority.HIGH,
                interruptible=False
            )
            
            # Brief pause to let audio resources reset
            await asyncio.sleep(0.1)
            
            # Start speech recognition
            await self._speech_recognizer.start_recognition()
            self._listening_state = ListeningState.LISTENING
            self._last_audio_time = time.time()
            
        except Exception as e:
            self._logger.error(f"Failed to transition to listening: {str(e)}")
            self._listening_state = ListeningState.ERROR
            
    async def _process_audio_input(self) -> None:
        """Process audio input during active listening."""
        try:
            # Check for timeout
            current_time = time.time()
            if current_time - self._last_audio_time > self.LISTEN_TIMEOUT:
                await self._handle_listen_timeout()
                return
                
            # Try to recognize speech
            text = await self._speech_recognizer.recognize()
            if text:
                self._last_audio_time = current_time
                await self._handle_command(text)
            elif current_time - self._last_audio_time > self.MAX_SILENCE:
                await self._handle_silence_timeout()
                
        except Exception as e:
            self._logger.error(f"Error processing audio input: {str(e)}")
            self._listening_state = ListeningState.ERROR
            
    async def _handle_command(self, text: str) -> None:
        """Handle recognized command."""
        self._listening_state = ListeningState.PROCESSING
        
        try:
            # Process the command (implement command parsing/handling)
            self._logger.info(f"Processing command: {text}")
            
            # Reset state after processing
            await self._reset_listening_state()
            
        except Exception as e:
            self._logger.error(f"Error handling command: {str(e)}")
            await self._queue_feedback(
                "Sorry, I couldn't process that command.",
                FeedbackCategory.ERROR,
                FeedbackPriority.NORMAL
            )
            self._listening_state = ListeningState.ERROR
            
    async def _handle_listen_timeout(self) -> None:
        """Handle listening timeout."""
        await self._queue_feedback(
            "I didn't hear anything.",
            FeedbackCategory.SYSTEM,
            FeedbackPriority.NORMAL
        )
        await self._reset_listening_state()
        
    async def _handle_silence_timeout(self) -> None:
        """Handle silence timeout."""
        await self._queue_feedback(
            "Listening timeout.",
            FeedbackCategory.SYSTEM,
            FeedbackPriority.NORMAL
        )
        await self._reset_listening_state()
        
    async def _reset_listening_state(self) -> None:
        """Reset to idle state."""
        if self._speech_recognizer:
            await self._speech_recognizer.stop_recognition()
            
        # Brief pause to let audio resources reset
        await asyncio.sleep(0.1)
        
        # Restart wake word detection
        await self._wake_word_detector.start_detection()
        self._listening_state = ListeningState.IDLE
        
    async def _queue_feedback(self, 
                            message: Union[str, Dict[str, Any]], 
                            category: FeedbackCategory,
                            priority: FeedbackPriority = FeedbackPriority.NORMAL,
                            task_type: Optional[TaskType] = None,
                            interruptible: bool = True) -> None:
        """Queue a feedback message with enhanced metadata."""
        if not self._feedback_config.enabled or \
           (self._feedback_config.silent_mode and priority != FeedbackPriority.CRITICAL):
            return
            
        # Create feedback message
        if isinstance(message, dict):
            feedback = FeedbackMessage(
                message['text'],
                message.get('category', category),
                message.get('priority', priority),
                task_type,
                interruptible
            )
        else:
            feedback = FeedbackMessage(message, category, priority, task_type, interruptible)
            
        # Handle high-priority interruptions
        if priority in {FeedbackPriority.CRITICAL, FeedbackPriority.HIGH} and \
           self._current_feedback and \
           self._current_feedback.interruptible and \
           self._current_feedback.priority > priority:
            await self._interrupt_current_feedback()
            
        self._feedback_queue.append(feedback)
        self._logger.debug(
            f"Queued feedback: {feedback.text} "
            f"(Priority: {feedback.priority.name}, Category: {feedback.category.name})"
        )
        
    async def _interrupt_current_feedback(self) -> None:
        """Interrupt current feedback for higher priority message."""
        if self._current_feedback and self._tts_engine:
            try:
                await self._tts_engine.stop_speaking()
                self._logger.debug("Interrupted current feedback for priority message")
            except Exception as e:
                self._logger.error(f"Failed to interrupt feedback: {str(e)}")
                
    async def _process_feedback_queue(self) -> None:
        """Process queued feedback messages with priority handling."""
        while self._running:
            try:
                if self._feedback_queue:
                    async with self._feedback_lock:
                        feedback = self._feedback_queue[0]
                        current_time = time.time()
                        
                        # Check timing and priority
                        if feedback.priority == FeedbackPriority.CRITICAL or \
                           current_time - self._last_feedback_time >= \
                           self._feedback_config.delay_between_messages:
                            self._current_feedback = feedback
                            await self._speak(feedback)
                            self._feedback_queue.popleft()
                            self._last_feedback_time = current_time
                            self._current_feedback = None
                            
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self._logger.error(f"Error processing feedback: {str(e)}")
                
    async def _speak(self, feedback: FeedbackMessage) -> None:
        """Speak feedback message with haptic support."""
        if not self._tts_engine:
            return
            
        try:
            # Provide haptic feedback if enabled
            if self._feedback_config.haptic_enabled and \
               feedback.priority in {FeedbackPriority.CRITICAL, FeedbackPriority.HIGH}:
                await self._provide_haptic_feedback()
                
            # Speak message
            await self._tts_engine.speak(
                feedback.text,
                volume=self._feedback_config.volume
            )
            
            self._logger.info(
                f"Spoke feedback: {feedback.text} "
                f"(Priority: {feedback.priority.name}, "
                f"Category: {feedback.category.name})"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to provide feedback: {str(e)}")
            
    async def _provide_haptic_feedback(self) -> None:
        """Provide haptic feedback."""
        # Implement haptic feedback here
        pass
        
    async def _process_with_retry(self,
                                task_type: TaskType,
                                data: Dict[str, Any],
                                priority: PriorityLevel) -> Optional[Any]:
        """Process task with retry mechanism."""
        max_retries = RetryConfig.MAX_RETRIES[priority]
        base_delay = RetryConfig.BASE_DELAY[priority]
        timeout = self._adaptive_timeouts[priority]
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                result = await asyncio.wait_for(
                    self._process_task(task_type, data),
                    timeout=timeout
                )
                
                # Success - adjust timeout if it was increased
                if timeout > self.BASE_TIMEOUTS[priority]:
                    self._adaptive_timeouts[priority] = max(
                        self.BASE_TIMEOUTS[priority],
                        timeout * 0.9  # Gradually reduce timeout
                    )
                    
                # Update success metrics
                duration = time.time() - start_time
                self._update_metrics(task_type, duration, False, False)
                return result
                
            except asyncio.TimeoutError:
                self._logger.warning(
                    f"Task {task_type.value} timed out (attempt {attempt + 1}/{max_retries})"
                )
                # Increase timeout for subsequent attempts
                timeout = min(timeout * 1.5, timeout + 30)
                self._adaptive_timeouts[priority] = timeout
                self._update_metrics(task_type, timeout, False, True)
                
            except Exception as e:
                self._logger.error(
                    f"Task {task_type.value} failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                self._update_metrics(task_type, time.time() - start_time, True, False)
                
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(delay)
                
        raise EdgeProcessingError(
            f"Task {task_type.value} failed after {max_retries} attempts"
        )
        
    def _update_metrics(self,
                       task_type: TaskType,
                       duration: float,
                       had_error: bool,
                       had_timeout: bool) -> None:
        """Update task performance metrics."""
        stats = self._stats[task_type.value]
        stats['duration_total'] += duration
        stats['duration_count'] += 1
        if had_error:
            stats['errors'] += 1
        if had_timeout:
            stats['timeouts'] += 1
            
        # Update performance metrics
        metrics = self._performance_metrics[task_type.value]
        metrics['avg_duration'] = stats['duration_total'] / stats['duration_count']
        metrics['error_rate'] = stats['errors'] / stats['duration_count']
        metrics['timeout_rate'] = stats['timeouts'] / stats['duration_count']
        
    async def _schedule_batch_processing(self, task_type: TaskType) -> None:
        """Schedule delayed batch processing for a task type."""
        if self._batch_timers[task_type]:
            self._batch_timers[task_type].cancel()
            
        self._batch_timers[task_type] = asyncio.create_task(
            self._process_batch_after_delay(task_type)
        )
        
    async def _process_batch_after_delay(self, task_type: TaskType) -> None:
        """Process batch after delay window."""
        try:
            await asyncio.sleep(BatchConfig.BATCH_WINDOW)
            await self._process_batch(task_type)
        except Exception as e:
            self._logger.error(f"Error processing batch for {task_type}: {str(e)}")
            
    async def _process_batch(self, task_type: TaskType) -> None:
        """Process a batch of tasks with fallback."""
        async with self._lock:
            if not self._batch_queues[task_type]:
                return
                
            batch = self._batch_queues[task_type]
            self._batch_queues[task_type] = []
            self._batch_timers[task_type] = None
            
        metrics = self._batch_metrics[task_type]
        start_time = time.time()
        
        try:
            # Process batch
            results = await self._process_batch_with_fallback(task_type, batch)
            
            # Update metrics
            metrics.total_time += time.time() - start_time
            metrics.batch_count += 1
            metrics.success_count += 1
            
            # Set results
            for (_, future), result in zip(batch, results):
                if not future.done():
                    future.set_result(result)
                    
        except Exception as e:
            metrics.failure_count += 1
            self._logger.error(f"Batch processing failed for {task_type}: {str(e)}")
            
            # Try individual processing as fallback
            await self._process_batch_individually(task_type, batch)
            
        finally:
            # Adjust batch configuration
            self._batch_configs[task_type].adjust(metrics)
            
    async def _process_batch_with_fallback(self, 
                                         task_type: TaskType,
                                         batch: List[Tuple[Dict[str, Any], asyncio.Future]]
                                         ) -> List[Any]:
        """Process batch with fallback mechanisms."""
        try:
            if task_type == TaskType.WEATHER:
                return await self._batch_process_weather([task[0] for task in batch])
            elif task_type == TaskType.CALENDAR:
                return await self._batch_process_calendar([task[0] for task in batch])
            else:
                raise ValueError(f"Unsupported batch type: {task_type}")
                
        except Exception as e:
            self._logger.warning(f"Batch processing failed, attempting fallback: {str(e)}")
            raise
            
    async def _process_batch_individually(self,
                                        task_type: TaskType,
                                        batch: List[Tuple[Dict[str, Any], asyncio.Future]]
                                        ) -> None:
        """Process batch items individually as fallback."""
        for data, future in batch:
            if future.done():
                continue
                
            try:
                # Try to process individually
                result = await self._process_task(task_type, data)
                future.set_result(result)
            except Exception as e:
                self._logger.error(
                    f"Individual processing failed for {task_type}: {str(e)}"
                )
                future.set_exception(e)
                
    async def _batch_process_weather(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple weather tasks together."""
        # Combine locations
        locations = {task['location'] for task in tasks}
        
        # Single API call for all locations
        try:
            # Implement actual weather fetching logic here
            results = [{"location": loc, "processed": True} for loc in locations]
            
            # Map results back to individual tasks
            return [
                next(r for r in results if r['location'] == task['location'])
                for task in tasks
            ]
        except Exception as e:
            self._logger.error(f"Weather batch processing failed: {str(e)}")
            raise
            
    async def _batch_process_calendar(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple calendar tasks together."""
        # Similar implementation for calendar batch processing
        return [{"event_type": task['event_type'], "processed": True} for task in tasks]
        
    async def _check_connectivity(self, task_type: TaskType) -> bool:
        """Check if task can run in current connectivity state."""
        connectivity = self.CONNECTIVITY_MAP[task_type]
        
        if connectivity == TaskConnectivity.OFFLINE:
            return True
        elif connectivity == TaskConnectivity.ONLINE and not self._connectivity_status:
            return False
        elif connectivity == TaskConnectivity.HYBRID:
            return True  # Can run with limited functionality
            
        return self._connectivity_status
        
    async def _get_cache_ttl(self, 
                            task_type: TaskType, 
                            is_fallback: bool = False) -> Optional[int]:
        """Get appropriate TTL based on connectivity and task type."""
        policy = self.CACHE_POLICIES.get(task_type)
        if not policy:
            return None
            
        if self._connectivity_status and not is_fallback:
            return policy.online_ttl
        return policy.offline_ttl
        
    async def _validate_cached_data(self,
                                  task_type: TaskType,
                                  cached_data: Dict[str, Any]) -> bool:
        """Validate cached data age against policy."""
        policy = self.CACHE_POLICIES.get(task_type)
        if not policy or not policy.max_age:
            return True
            
        timestamp = cached_data.get('timestamp', 0)
        age = time.time() - timestamp
        return age <= policy.max_age
        
    async def _get_offline_fallback(self,
                                  task_type: TaskType,
                                  data: Dict[str, Any],
                                  cache_key: Optional[str] = None) -> Tuple[Optional[Any], str]:
        """Get offline fallback data with voice feedback."""
        if task_type == TaskType.WEATHER and cache_key:
            cached_data = await self._cache.get(cache_key)
            if cached_data and await self._validate_cached_data(task_type, cached_data):
                return cached_data, self.VOICE_MESSAGES['weather_cached']
                
        elif task_type == TaskType.CALENDAR:
            if data.get('action') == 'view_events':
                local_events = await self._get_local_calendar_data(data)
                if local_events:
                    return local_events, self.VOICE_MESSAGES['calendar_offline']
                    
        return None, self.VOICE_MESSAGES.get(task_type.value, "This feature is unavailable offline.")
        
    async def _get_local_calendar_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve local calendar data."""
        # Implement local calendar storage/retrieval
        return {"event_type": "local", "events": []}
        
    async def process_locally(self,
                            task_type: Union[TaskType, str],
                            data: Dict[str, Any],
                            cache_key: Optional[str] = None,
                            ttl: Optional[int] = None) -> Optional[Any]:
        """Process task with voice feedback."""
        task_type = TaskType[task_type.upper()] if isinstance(task_type, str) else task_type
        
        # Check connectivity and capabilities
        can_process = await self._check_connectivity(task_type)
        if not can_process:
            message = self.OFFLINE_MESSAGES.get(task_type, "This feature requires internet connection.")
            await self._speak(message)
            
            fallback_data, feedback = await self._get_offline_fallback(
                task_type, data, cache_key
            )
            if feedback:
                await self._speak(feedback)
            return fallback_data
            
        try:
            # Acknowledge long-running tasks
            if task_type in {TaskType.WEATHER, TaskType.CALENDAR}:
                await self._speak(self.VOICE_MESSAGES['processing'])
                
            result = await self._process_with_retry(task_type, data)
            
            # Provide success feedback if needed
            if result and isinstance(result, dict) and result.get('feedback'):
                await self._speak(result['feedback'])
                
            return result
            
        except asyncio.TimeoutError:
            await self._speak(self.VOICE_MESSAGES['timeout'])
            raise
        except Exception as e:
            await self._speak(self.VOICE_MESSAGES['task_error'])
            raise
            
    async def stop(self) -> None:
        """Stop processor and all components."""
        if self._running:
            self._running = False
            
            # Stop listening task first
            if self._listening_task:
                self._listening_task.cancel()
                try:
                    await self._listening_task
                except asyncio.CancelledError:
                    pass
                    
            # Stop recognition components
            if self._speech_recognizer:
                await self._speech_recognizer.cleanup()
            if self._wake_word_detector:
                await self._wake_word_detector.cleanup()
                
            # Simple shutdown message
            if self._tts_engine:
                try:
                    await self._tts_engine.speak("Shutting down")
                except:
                    pass
                await self._tts_engine.cleanup()
                
            await self._cache.stop()
            
    async def _wait_pending_feedback(self) -> None:
        """Wait for pending feedback messages to complete."""
        while self._feedback_queue and self._running:
            await asyncio.sleep(0.1)

    def enable_voice_feedback(self, enabled: bool = True) -> None:
        """Enable or disable voice feedback."""
        self._voice_feedback_enabled = enabled

    def is_listening(self) -> bool:
        """Check if processor is currently listening for commands."""
        return self._listening_state == ListeningState.LISTENING

    def _initialize_stats(self) -> Dict[str, Dict[str, int]]:
        """Initialize statistics tracking."""
        return {
            task_type.value: {
                'processed': 0,
                'cached': 0,
                'errors': 0,
                'timeouts': 0,
                'duration_total': 0,
                'duration_count': 0
            }
            for task_type in TaskType
        }
