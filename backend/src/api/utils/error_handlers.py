"""
Shared error handling utilities and decorators.
Eliminates duplicate error handling patterns across routers and services.
"""
import logging
from functools import wraps
from typing import Any, Callable, TypeVar
from fastapi import HTTPException, status

from src.api.core.exceptions import BotOperationError

logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


def handle_service_errors(
    operation_name: str = None,
    custom_error_message: str = None
) -> Callable[[F], F]:
    """
    Decorator that standardizes error handling for service operations.
    
    Args:
        operation_name: Name of the operation for logging
        custom_error_message: Custom error message prefix
        
    Returns:
        Decorated function with standardized error handling
        
    Usage:
        @handle_service_errors("create bot")
        async def create_bot(...):
            # Implementation
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions (they're already properly formatted)
                raise
            except Exception as e:
                # Log the error with context
                op_name = operation_name or func.__name__
                logger.error(f"Error in {op_name}: {str(e)}", exc_info=True)
                
                # Create standardized error message
                if custom_error_message:
                    error_detail = f"{custom_error_message}: {str(e)}"
                else:
                    error_detail = f"Failed to {op_name}: {str(e)}"
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_detail
                )
        
        return wrapper
    return decorator


def handle_router_errors(
    operation_name: str = None
) -> Callable[[F], F]:
    """
    Decorator specifically for router endpoints that standardizes error handling.
    
    Args:
        operation_name: Name of the operation for logging
        
    Returns:
        Decorated function with router-specific error handling
        
    Usage:
        @handle_router_errors("create bot instance")
        async def create_bot_instance(...):
            # Implementation
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                # Log the error
                op_name = operation_name or func.__name__
                logger.error(f"Router error in {op_name}: {str(e)}", exc_info=True)
                
                # Return generic 500 error for security
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal server error during {op_name}"
                )
        
        return wrapper
    return decorator


class ErrorContext:
    """
    Context manager for handling errors with additional context.
    
    Usage:
        async with ErrorContext("updating bot", bot_id="123"):
            # Operations that might fail
            await some_operation()
    """
    
    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and exc_type != HTTPException:
            # Log error with context
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            logger.error(
                f"Error {self.operation} ({context_str}): {str(exc_val)}", 
                exc_info=True
            )
            
            # Convert to standardized error
            raise BotOperationError(
                detail=f"Failed {self.operation}: {str(exc_val)}"
            ) from exc_val
        
        # Let HTTP exceptions pass through unchanged
        return False


def log_operation_start(operation: str, **context):
    """
    Log the start of an operation with context.
    
    Args:
        operation: Description of the operation
        **context: Additional context to log
    """
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.info(f"Starting {operation} ({context_str})")


def log_operation_success(operation: str, **context):
    """
    Log successful completion of an operation.
    
    Args:
        operation: Description of the operation
        **context: Additional context to log
    """
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    logger.info(f"Successfully completed {operation} ({context_str})")


def validate_uuid(value: str, field_name: str = "ID") -> None:
    """
    Validate that a string is a valid UUID.
    
    Args:
        value: String to validate
        field_name: Name of the field for error messages
        
    Raises:
        HTTPException: If value is not a valid UUID
    """
    try:
        from uuid import UUID
        UUID(value)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format. Must be a valid UUID."
        )