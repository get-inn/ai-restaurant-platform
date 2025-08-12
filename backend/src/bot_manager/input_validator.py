"""
Input Validation System for Bot Management

This module provides comprehensive input validation for bot conversations to handle
duplicate button clicks, invalid inputs, and edge cases that can cause scenarios
to malfunction or skip steps unexpectedly.

Features:
1. Duplicate submission detection using Redis caching
2. Rate limiting to prevent abuse
3. Button validation against expected options
4. Input type validation (text vs buttons)
5. Dialog state consistency checks
6. User-friendly error messages and corrections
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class InputType(Enum):
    BUTTON_CLICK = "button_click"
    TEXT_MESSAGE = "text_message"
    MEDIA_MESSAGE = "media_message"
    COMMAND = "command"

class ValidationResult(Enum):
    VALID = "valid"
    DUPLICATE = "duplicate"
    INVALID_BUTTON = "invalid_button"
    WRONG_INPUT_TYPE = "wrong_input_type"
    STATE_MISMATCH = "state_mismatch"
    RATE_LIMITED = "rate_limited"

@dataclass
class ValidationContext:
    user_id: str
    bot_id: str
    platform: str
    platform_chat_id: str
    input_type: InputType
    input_value: Any
    expected_buttons: Optional[List[Dict[str, Any]]]
    current_step: str
    dialog_state: Dict[str, Any]
    timestamp: datetime

@dataclass
class ValidationResponse:
    result: ValidationResult
    is_valid: bool
    error_message: Optional[str] = None
    correction_message: Optional[str] = None
    should_retry_current_step: bool = False
    suggested_buttons: Optional[List[Dict[str, Any]]] = None

class InputValidator:
    def __init__(self, redis_client=None, duplicate_window_seconds: int = 2):
        self.redis_client = redis_client
        self.duplicate_window = duplicate_window_seconds
        self.duplicate_cache = {}  # Fallback for development
        
    async def validate_input(self, context: ValidationContext) -> ValidationResponse:
        """
        Main validation entry point.
        Performs comprehensive input validation.
        """
        try:
            # 1. Check for duplicate submissions
            duplicate_check = await self._check_duplicate_submission(context)
            if duplicate_check.result == ValidationResult.DUPLICATE:
                return duplicate_check
                
            # 2. Check rate limiting
            rate_check = await self._check_rate_limit(context)
            if rate_check.result == ValidationResult.RATE_LIMITED:
                return rate_check
                
            # 3. Validate dialog state consistency
            state_check = await self._validate_dialog_state(context)
            if state_check.result == ValidationResult.STATE_MISMATCH:
                return state_check
                
            # 4. Validate input type and content
            input_check = await self._validate_input_content(context)
            if input_check.result != ValidationResult.VALID:
                return input_check
                
            # 5. Record successful validation
            await self._record_valid_input(context)
            
            return ValidationResponse(
                result=ValidationResult.VALID,
                is_valid=True
            )
            
        except Exception as e:
            logger.error(f"Error during input validation: {str(e)}", exc_info=True)
            # Return a generic error response instead of raising
            return ValidationResponse(
                result=ValidationResult.STATE_MISMATCH,
                is_valid=False,
                error_message="Validation error occurred",
                correction_message="Something went wrong. Please try again or use /start to restart.",
                should_retry_current_step=False
            )
    
    async def _check_duplicate_submission(
        self, 
        context: ValidationContext
    ) -> ValidationResponse:
        """
        Check if this input is a duplicate of a recent submission.
        Uses content hash + timing to detect duplicates.
        """
        # Create unique key for this input
        input_hash = self._create_input_hash(context)
        cache_key = f"input:{context.bot_id}:{context.user_id}:{input_hash}"
        
        # Check if we've seen this input recently
        if self.redis_client:
            try:
                last_seen = await self.redis_client.get(cache_key)
                if last_seen:
                    last_timestamp = datetime.fromisoformat(last_seen.decode())
                    if context.timestamp - last_timestamp < timedelta(seconds=self.duplicate_window):
                        return ValidationResponse(
                            result=ValidationResult.DUPLICATE,
                            is_valid=False,
                            correction_message="⚠️ Please wait a moment before clicking again.",
                            should_retry_current_step=False
                        )
            except Exception as e:
                logger.warning(f"Redis duplicate check failed: {e}")
                # Fall through to local cache check
        
        # Fallback for development or Redis failure
        if cache_key in self.duplicate_cache:
            last_timestamp = self.duplicate_cache[cache_key]
            if context.timestamp - last_timestamp < timedelta(seconds=self.duplicate_window):
                return ValidationResponse(
                    result=ValidationResult.DUPLICATE,
                    is_valid=False,
                    correction_message="⚠️ Please wait a moment before clicking again.",
                    should_retry_current_step=False
                )
        
        return ValidationResponse(result=ValidationResult.VALID, is_valid=True)
    
    async def _check_rate_limit(self, context: ValidationContext) -> ValidationResponse:
        """
        Check if user is sending inputs too frequently.
        """
        rate_key = f"rate:{context.bot_id}:{context.user_id}"
        max_requests_per_minute = 30
        
        if self.redis_client:
            try:
                current_count = await self.redis_client.incr(rate_key)
                if current_count == 1:
                    await self.redis_client.expire(rate_key, 60)  # 1 minute window
                
                if current_count > max_requests_per_minute:
                    return ValidationResponse(
                        result=ValidationResult.RATE_LIMITED,
                        is_valid=False,
                        correction_message="⚠️ You're sending messages too quickly. Please slow down.",
                        should_retry_current_step=False
                    )
            except Exception as e:
                logger.warning(f"Redis rate limit check failed: {e}")
                # Continue without rate limiting if Redis fails
        
        return ValidationResponse(result=ValidationResult.VALID, is_valid=True)
    
    async def _validate_dialog_state(
        self, 
        context: ValidationContext
    ) -> ValidationResponse:
        """
        Validate that the dialog state is consistent and expected.
        """
        # Check if dialog state exists
        if context.dialog_state is None:
            return ValidationResponse(
                result=ValidationResult.STATE_MISMATCH,
                is_valid=False,
                error_message="Dialog state not found",
                correction_message="Let's start over. Please use /start to begin.",
                should_retry_current_step=False
            )
        
        # Check if current step matches expected step
        if not context.current_step:
            return ValidationResponse(
                result=ValidationResult.STATE_MISMATCH,
                is_valid=False,
                error_message="Current step not defined",
                correction_message="Something went wrong. Let me help you continue.",
                should_retry_current_step=True
            )
        
        return ValidationResponse(result=ValidationResult.VALID, is_valid=True)
    
    async def _validate_input_content(
        self, 
        context: ValidationContext
    ) -> ValidationResponse:
        """
        Validate the actual input content against expected format.
        """
        if context.input_type == InputType.BUTTON_CLICK:
            return await self._validate_button_input(context)
        elif context.input_type == InputType.TEXT_MESSAGE:
            return await self._validate_text_input(context)
        elif context.input_type == InputType.COMMAND:
            return await self._validate_command_input(context)
        
        return ValidationResponse(result=ValidationResult.VALID, is_valid=True)
    
    async def _validate_button_input(
        self, 
        context: ValidationContext
    ) -> ValidationResponse:
        """
        Validate button click against expected buttons for current step.
        """
        if not context.expected_buttons:
            # No buttons expected, but button was clicked
            return ValidationResponse(
                result=ValidationResult.WRONG_INPUT_TYPE,
                is_valid=False,
                correction_message="Please send a text message instead of clicking a button.",
                should_retry_current_step=True
            )
        
        # Check if clicked button value is in expected buttons
        button_values = [btn.get('value') for btn in context.expected_buttons]
        if context.input_value not in button_values:
            # Create user-friendly button list
            button_texts = [btn.get('text', btn.get('value', 'Unknown')) 
                           for btn in context.expected_buttons]
            
            return ValidationResponse(
                result=ValidationResult.INVALID_BUTTON,
                is_valid=False,
                correction_message=f"Please choose one of these options: {', '.join(button_texts)}",
                should_retry_current_step=True,
                suggested_buttons=context.expected_buttons
            )
        
        return ValidationResponse(result=ValidationResult.VALID, is_valid=True)
    
    async def _validate_text_input(
        self, 
        context: ValidationContext
    ) -> ValidationResponse:
        """
        Validate text input when text is expected.
        """
        if context.expected_buttons:
            # Buttons are expected, but text was provided
            button_texts = [btn.get('text', btn.get('value', 'Unknown')) 
                           for btn in context.expected_buttons]
            
            return ValidationResponse(
                result=ValidationResult.WRONG_INPUT_TYPE,
                is_valid=False,
                correction_message=f"Please click one of these buttons: {', '.join(button_texts)}",
                should_retry_current_step=True,
                suggested_buttons=context.expected_buttons
            )
        
        # Additional text validation can be added here
        # (length, format, content rules, etc.)
        
        return ValidationResponse(result=ValidationResult.VALID, is_valid=True)
    
    async def _validate_command_input(
        self, 
        context: ValidationContext
    ) -> ValidationResponse:
        """
        Validate command input (like /start, /help).
        Commands are generally always valid and can interrupt flows.
        """
        return ValidationResponse(result=ValidationResult.VALID, is_valid=True)
    
    def _create_input_hash(self, context: ValidationContext) -> str:
        """
        Create a hash of the input content for duplicate detection.
        """
        content = f"{context.input_type.value}:{context.input_value}:{context.current_step}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def _record_valid_input(self, context: ValidationContext):
        """
        Record this input as processed to prevent duplicates.
        """
        input_hash = self._create_input_hash(context)
        cache_key = f"input:{context.bot_id}:{context.user_id}:{input_hash}"
        
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key, 
                    self.duplicate_window, 
                    context.timestamp.isoformat()
                )
            except Exception as e:
                logger.warning(f"Redis record input failed: {e}")
                # Fall through to local cache
        
        # Always update local cache as fallback
        self.duplicate_cache[cache_key] = context.timestamp
        
        # Clean old entries periodically
        cutoff = context.timestamp - timedelta(seconds=self.duplicate_window * 2)
        self.duplicate_cache = {
            k: v for k, v in self.duplicate_cache.items() 
            if v > cutoff
        }