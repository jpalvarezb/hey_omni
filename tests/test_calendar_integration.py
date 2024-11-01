"""Tests for calendar integration."""
import pytest
from datetime import datetime, timedelta
from omni.core.config import Config
from omni.models.intent import Intent, IntentType, IntentSlot
from omni.services.intent.handlers.calendar_handler import CalendarHandler
from omni.services.cloud.api.calendar_service import CalendarAPI
from omni.core.exceptions import CalendarError, AuthError