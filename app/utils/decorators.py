
"""
File: app/utils/decorators.py

Module Description:
    Custom decorators for the OT Video Management System.
    
    Provides reusable decorators for:
    - Error handling and logging
    - Retry logic
    - Performance timing
    - Input validation
    - Thread safety
    
    Decorators simplify code by extracting common patterns into reusable
    functions that can be applied to any function/method.

Dependencies:
    - functools: For preserving function metadata
    - time: For timing and delays
    - threading: For thread locks

Usage Example:
    >>> from app.utils.decorators import log_errors, retry
    >>> 
    >>> @log_errors
    ... @retry(max_attempts=3)
    ... def risky_operation():
    ...     # code that might fail
    ...     pass

Author: OT Video Dev Team
Date: January 28, 2026
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
import functools
import time
import threading
from typing import Callable, Any, Optional

from app.utils.logger import AppLogger

# Initialize module logger
logger = AppLogger("Decorators")


# ============================================================================
# ERROR HANDLING DECORATORS
# ============================================================================
def log_errors(func: Callable) -> Callable:
    """
    Decorator to log exceptions without suppressing them.
    
    Logs the exception with full traceback but still raises it
    for caller to handle. Useful for debugging and monitoring.
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    
    Example:
        >>> @log_errors
        ... def divide(a, b):
        ...     return a / b
        >>> 
        >>> divide(10, 0)  # Logs error and raises ZeroDivisionError
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {e}")
            raise  # Re-raise exception after logging
    
    return wrapper


def catch_errors(default_return: Any = None, 
                 log_exception: bool = True) -> Callable:
    """
    Decorator to catch and suppress exceptions, returning default value.
    
    Use when you want function to never fail, returning a safe default
    instead. Good for UI code where crash is worse than missing data.
    
    Args:
        default_return: Value to return on exception
        log_exception: Whether to log the exception
    
    Returns:
        Decorator function
    
    Example:
        >>> @catch_errors(default_return=0)
        ... def get_file_size(path):
        ...     return os.path.getsize(path)
        >>> 
        >>> size = get_file_size("nonexistent.txt")
        >>> print(size)
        0  # Returns default instead of crashing
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_exception:
                    logger.exception(f"Caught error in {func.__name__}: {e}")
                return default_return
        
        return wrapper
    
    return decorator


# ============================================================================
# RETRY DECORATOR
# ============================================================================
def retry(max_attempts: int = 3, 
          delay: float = 1.0,
          backoff: float = 2.0,
          exceptions: tuple = (Exception,)) -> Callable:
    """
    Decorator to retry function on failure.
    
    Retries function up to max_attempts times with exponential backoff.
    Useful for operations that might fail due to transient issues
    (network, hardware, timing).
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Backoff multiplier for delay (default: 2.0)
                Delay doubles each retry: 1s, 2s, 4s, 8s...
        exceptions: Tuple of exceptions to catch (default: all exceptions)
    
    Returns:
        Decorator function
    
    Example:
        >>> @retry(max_attempts=3, delay=0.5, backoff=2.0)
        ... def connect_to_device():
        ...     # Might fail on first attempt
        ...     device.open()
        >>> 
        >>> connect_to_device()  # Retries up to 3 times
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise  # Final attempt failed, raise exception
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay}s: {e}"
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
        
        return wrapper
    
    return decorator


# ============================================================================
# PERFORMANCE DECORATORS
# ============================================================================
def timer(func: Callable) -> Callable:
    """
    Decorator to time function execution.
    
    Logs execution time in debug mode. Useful for identifying slow functions.
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    
    Example:
        >>> @timer
        ... def process_video():
        ...     # Processing code
        ...     time.sleep(2)
        >>> 
        >>> process_video()
        # Logs: "process_video took 2.00 seconds"
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        logger.debug(f"{func.__name__} took {elapsed:.2f} seconds")
        
        return result
    
    return wrapper


def profile(func: Callable) -> Callable:
    """
    Decorator to profile function (execution time and call count).
    
    Tracks how many times function is called and total/average time.
    Stores stats in function attributes.
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    
    Example:
        >>> @profile
        ... def encode_frame():
        ...     # Encoding code
        ...     pass
        >>> 
        >>> # After multiple calls:
        >>> print(f"Called {encode_frame.call_count} times")
        >>> print(f"Average time: {encode_frame.avg_time:.3f}s")
    """
    # Initialize stats
    func.call_count = 0
    func.total_time = 0.0
    func.avg_time = 0.0
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        # Update stats
        func.call_count += 1
        func.total_time += elapsed
        func.avg_time = func.total_time / func.call_count
        
        logger.debug(
            f"{func.__name__} call #{func.call_count}: {elapsed:.3f}s "
            f"(avg: {func.avg_time:.3f}s)"
        )
        
        return result
    
    return wrapper


# ============================================================================
# THREAD SAFETY DECORATORS
# ============================================================================
def synchronized(lock: Optional[threading.Lock] = None) -> Callable:
    """
    Decorator to make function thread-safe.
    
    Ensures only one thread can execute function at a time.
    Useful for functions that modify shared state.
    
    Args:
        lock: Threading lock to use (creates new one if not provided)
    
    Returns:
        Decorator function
    
    Example:
        >>> # Shared lock for multiple functions
        >>> shared_lock = threading.Lock()
        >>> 
        >>> @synchronized(shared_lock)
        ... def update_counter():
        ...     global counter
        ...     counter += 1
        >>> 
        >>> @synchronized(shared_lock)
        ... def read_counter():
        ...     return counter
    """
    # Create lock if not provided
    if lock is None:
        lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# VALIDATION DECORATORS
# ============================================================================
def validate_args(**validators) -> Callable:
    """
    Decorator to validate function arguments.
    
    Checks arguments against validation functions before execution.
    
    Args:
        **validators: Keyword arguments mapping parameter names to
                     validation functions. Validation function should
                     return (is_valid, error_message) tuple.
    
    Returns:
        Decorator function
    
    Example:
        >>> from app.utils.validation import validate_patient_name
        >>> 
        >>> @validate_args(name=validate_patient_name)
        ... def save_patient(name):
        ...     # Save patient
        ...     pass
        >>> 
        >>> save_patient("John@Smith")  # Raises ValueError
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            
            # Validate each argument
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    is_valid, error = validator(value)
                    
                    if not is_valid:
                        raise ValueError(f"Invalid {param_name}: {error}")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# DEPRECATION DECORATOR
# ============================================================================
def deprecated(reason: str = "", alternative: str = "") -> Callable:
    """
    Decorator to mark function as deprecated.
    
    Logs warning when deprecated function is called.
    
    Args:
        reason: Why function is deprecated
        alternative: Suggested alternative function
    
    Returns:
        Decorator function
    
    Example:
        >>> @deprecated(
        ...     reason="Use new API",
        ...     alternative="new_save_video()"
        ... )
        ... def save_video_old():
        ...     pass
        >>> 
        >>> save_video_old()  # Logs deprecation warning
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__} is deprecated"
            
            if reason:
                message += f": {reason}"
            
            if alternative:
                message += f". Use {alternative} instead"
            
            logger.warning(message)
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# CACHING DECORATOR
# ============================================================================
def memoize(func: Callable) -> Callable:
    """
    Decorator to cache function results.
    
    Caches return values based on arguments. Useful for expensive
    computations with same inputs.
    
    Note: Only works with hashable arguments (no lists, dicts).
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    
    Example:
        >>> @memoize
        ... def expensive_calculation(n):
        ...     time.sleep(1)  # Simulate expensive operation
        ...     return n * 2
        >>> 
        >>> result = expensive_calculation(5)  # Takes 1 second
        >>> result = expensive_calculation(5)  # Returns instantly (cached)
    """
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from arguments
        key = str(args) + str(sorted(kwargs.items()))
        
        if key not in cache:
            cache[key] = func(*args, **kwargs)
            logger.debug(f"Cached result for {func.__name__}{args}")
        else:
            logger.debug(f"Using cached result for {func.__name__}{args}")
        
        return cache[key]
    
    return wrapper


# ============================================================================
# EXPORT
# ============================================================================
__all__ = [
    # Error handling
    'log_errors',
    'catch_errors',
    'retry',
    
    # Performance
    'timer',
    'profile',
    
    # Thread safety
    'synchronized',
    
    # Validation
    'validate_args',
    
    # Deprecation
    'deprecated',
    
    # Caching
    'memoize',
]


