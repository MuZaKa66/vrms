

"""
File: app/utils/validation.py

Module Description:
    Input validation and sanitization utilities for the OT Video Management System.
    
    Provides functions for:
    - Patient name validation and sanitization
    - Filename validation and sanitization
    - Input length validation
    - Pattern matching
    - Safe string handling
    
    All validation functions return (is_valid, error_message) tuples or
    sanitized strings depending on function purpose.

Dependencies:
    - re: Regular expressions for pattern matching
    - string: String constants

Usage Example:
    >>> from app.utils.validation import validate_patient_name, sanitize_filename
    >>> valid, error = validate_patient_name("John Smith")
    >>> if not valid:
    ...     print(f"Error: {error}")
    >>> 
    >>> safe_filename = sanitize_filename("patient: test/file")
    >>> print(safe_filename)
    patient_test_file

Author: OT Video Dev Team
Date: January 28, 2026
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
import re
import string
from typing import Tuple, Optional

from app.utils.logger import AppLogger
from app.utils.constants import (
    MAX_PATIENT_NAME_LENGTH,
    MAX_PROCEDURE_NAME_LENGTH,
    MAX_SURGEON_NAME_LENGTH,
    MAX_NOTES_LENGTH,
    MAX_TAG_LENGTH,
    MAX_FILENAME_LENGTH,
    PATIENT_NAME_PATTERN,
    FILENAME_SAFE_PATTERN
)

# Initialize module logger
logger = AppLogger("Validation")


# ============================================================================
# NAME VALIDATION FUNCTIONS
# ============================================================================
def validate_patient_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate patient name.
    
    Rules:
    - Not empty
    - Length <= MAX_PATIENT_NAME_LENGTH
    - Only alphanumeric, spaces, hyphens, dots
    - No special characters
    
    Args:
        name: Patient name to validate
    
    Returns:
        tuple: (is_valid, error_message)
               is_valid is True if valid, False otherwise
               error_message is None if valid, error string if invalid
    
    Example:
        >>> valid, error = validate_patient_name("John Smith")
        >>> print(valid)
        True
        
        >>> valid, error = validate_patient_name("Patient@123")
        >>> print(error)
        Patient name contains invalid characters
    """
    # Check if empty
    if not name or not name.strip():
        return False, "Patient name cannot be empty"
    
    # Check length
    if len(name) > MAX_PATIENT_NAME_LENGTH:
        return False, f"Patient name too long (max {MAX_PATIENT_NAME_LENGTH} characters)"
    
    # Check pattern (alphanumeric, spaces, hyphens, dots only)
    if not re.match(PATIENT_NAME_PATTERN, name):
        return False, "Patient name contains invalid characters"
    
    # Valid
    return True, None


def validate_procedure_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate procedure name.
    
    Rules:
    - Not empty
    - Length <= MAX_PROCEDURE_NAME_LENGTH
    - Printable characters only
    
    Args:
        name: Procedure name to validate
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_procedure_name("Cataract Surgery")
        >>> print(valid)
        True
    """
    if not name or not name.strip():
        return False, "Procedure name cannot be empty"
    
    if len(name) > MAX_PROCEDURE_NAME_LENGTH:
        return False, f"Procedure name too long (max {MAX_PROCEDURE_NAME_LENGTH} characters)"
    
    # Check for printable characters only
    if not all(c in string.printable for c in name):
        return False, "Procedure name contains invalid characters"
    
    return True, None


def validate_surgeon_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate surgeon name.
    
    Rules:
    - Can be empty (optional field)
    - If provided, length <= MAX_SURGEON_NAME_LENGTH
    - Only alphanumeric, spaces, hyphens, dots
    
    Args:
        name: Surgeon name to validate
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_surgeon_name("Dr. Smith")
        >>> print(valid)
        True
        
        >>> valid, error = validate_surgeon_name("")
        >>> print(valid)
        True  # Empty is allowed
    """
    # Empty is allowed for surgeon name (optional field)
    if not name or not name.strip():
        return True, None
    
    if len(name) > MAX_SURGEON_NAME_LENGTH:
        return False, f"Surgeon name too long (max {MAX_SURGEON_NAME_LENGTH} characters)"
    
    if not re.match(PATIENT_NAME_PATTERN, name):
        return False, "Surgeon name contains invalid characters"
    
    return True, None


def validate_notes(notes: str) -> Tuple[bool, Optional[str]]:
    """
    Validate notes text.
    
    Rules:
    - Can be empty (optional field)
    - Length <= MAX_NOTES_LENGTH
    - Printable characters only
    
    Args:
        notes: Notes text to validate
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_notes("Patient had complications")
        >>> print(valid)
        True
    """
    # Empty is allowed
    if not notes:
        return True, None
    
    if len(notes) > MAX_NOTES_LENGTH:
        return False, f"Notes too long (max {MAX_NOTES_LENGTH} characters)"
    
    # Check for printable characters only (allows newlines and tabs)
    if not all(c in string.printable for c in notes):
        return False, "Notes contain invalid characters"
    
    return True, None


def validate_tag(tag: str) -> Tuple[bool, Optional[str]]:
    """
    Validate tag text.
    
    Rules:
    - Not empty
    - Length <= MAX_TAG_LENGTH
    - Alphanumeric, spaces, hyphens, underscores only
    - No leading/trailing spaces
    
    Args:
        tag: Tag text to validate
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_tag("Emergency")
        >>> print(valid)
        True
    """
    if not tag or not tag.strip():
        return False, "Tag cannot be empty"
    
    if tag != tag.strip():
        return False, "Tag cannot have leading or trailing spaces"
    
    if len(tag) > MAX_TAG_LENGTH:
        return False, f"Tag too long (max {MAX_TAG_LENGTH} characters)"
    
    # Allow alphanumeric, spaces, hyphens, underscores
    pattern = r'^[A-Za-z0-9\s\-_]+$'
    if not re.match(pattern, tag):
        return False, "Tag contains invalid characters"
    
    return True, None


# ============================================================================
# FILENAME VALIDATION
# ============================================================================
def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate filename.
    
    Rules:
    - Not empty
    - Length <= MAX_FILENAME_LENGTH
    - No path separators (/, \)
    - Safe characters only (alphanumeric, _, -, .)
    - Has valid extension
    
    Args:
        filename: Filename to validate
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_filename("video_001.mp4")
        >>> print(valid)
        True
        
        >>> valid, error = validate_filename("../../../etc/passwd")
        >>> print(error)
        Filename contains path separators
    """
    if not filename or not filename.strip():
        return False, "Filename cannot be empty"
    
    if len(filename) > MAX_FILENAME_LENGTH:
        return False, f"Filename too long (max {MAX_FILENAME_LENGTH} characters)"
    
    # Check for path separators (security)
    if '/' in filename or '\\' in filename:
        return False, "Filename contains path separators"
    
    # Check for safe characters only
    if not re.match(FILENAME_SAFE_PATTERN, filename):
        return False, "Filename contains invalid characters"
    
    # Check for extension
    if '.' not in filename:
        return False, "Filename must have an extension"
    
    return True, None


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitize filename by replacing invalid characters.
    
    Makes filename safe for filesystem by:
    - Replacing invalid characters with replacement character
    - Removing path separators
    - Trimming to max length
    - Converting to ASCII
    
    Args:
        filename: Original filename
        replacement: Character to replace invalid chars with (default: '_')
    
    Returns:
        str: Sanitized filename
    
    Example:
        >>> sanitize_filename("patient: John/Smith.mp4")
        'patient_John_Smith.mp4'
        
        >>> sanitize_filename("video #1 (test).mp4")
        'video_1_test.mp4'
    """
    # Invalid characters for filenames
    invalid_chars = '<>:"/\\|?*'
    
    # Replace invalid characters
    for char in invalid_chars:
        filename = filename.replace(char, replacement)
    
    # Remove control characters
    filename = ''.join(c for c in filename if ord(c) >= 32)
    
    # Convert to ASCII (remove non-ASCII characters)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Replace multiple consecutive replacement chars with single
    while replacement + replacement in filename:
        filename = filename.replace(replacement + replacement, replacement)
    
    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        # Try to preserve extension
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = MAX_FILENAME_LENGTH - len(ext) - 1 if ext else MAX_FILENAME_LENGTH
        name = name[:max_name_length]
        filename = f"{name}.{ext}" if ext else name
    
    return filename


# ============================================================================
# GENERAL VALIDATION
# ============================================================================
def validate_string_length(text: str, min_length: int = 0, 
                          max_length: int = 1000, 
                          field_name: str = "Text") -> Tuple[bool, Optional[str]]:
    """
    Validate string length.
    
    Generic length validation for any text field.
    
    Args:
        text: Text to validate
        min_length: Minimum allowed length (default: 0)
        max_length: Maximum allowed length (default: 1000)
        field_name: Name of field for error messages
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_string_length("test", min_length=5, field_name="Password")
        >>> print(error)
        Password must be at least 5 characters
    """
    if text is None:
        text = ""
    
    length = len(text)
    
    if length < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    
    if length > max_length:
        return False, f"{field_name} cannot exceed {max_length} characters"
    
    return True, None


def validate_not_empty(text: str, field_name: str = "Field") -> Tuple[bool, Optional[str]]:
    """
    Validate that text is not empty.
    
    Args:
        text: Text to validate
        field_name: Name of field for error message
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_not_empty("", "Patient name")
        >>> print(error)
        Patient name cannot be empty
    """
    if not text or not text.strip():
        return False, f"{field_name} cannot be empty"
    
    return True, None


def validate_pattern(text: str, pattern: str, field_name: str = "Field") -> Tuple[bool, Optional[str]]:
    """
    Validate text against regex pattern.
    
    Args:
        text: Text to validate
        pattern: Regular expression pattern
        field_name: Name of field for error message
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_pattern("abc123", r'^[a-z]+$', "Username")
        >>> print(error)
        Username format is invalid
    """
    if not re.match(pattern, text):
        return False, f"{field_name} format is invalid"
    
    return True, None


# ============================================================================
# SANITIZATION FUNCTIONS
# ============================================================================
def sanitize_string(text: str, 
                    max_length: Optional[int] = None,
                    strip: bool = True,
                    lowercase: bool = False) -> str:
    """
    Sanitize general string input.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length (truncates if longer)
        strip: Remove leading/trailing whitespace
        lowercase: Convert to lowercase
    
    Returns:
        str: Sanitized text
    
    Example:
        >>> sanitize_string("  Test String  ", max_length=10, strip=True)
        'Test Strin'
        
        >>> sanitize_string("  MiXeD CaSe  ", strip=True, lowercase=True)
        'mixed case'
    """
    if text is None:
        return ""
    
    # Strip whitespace
    if strip:
        text = text.strip()
    
    # Convert case
    if lowercase:
        text = text.lower()
    
    # Truncate length
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def remove_special_characters(text: str, allowed: str = '') -> str:
    """
    Remove special characters from text.
    
    Keeps only alphanumeric, spaces, and specified allowed characters.
    
    Args:
        text: Text to clean
        allowed: String of allowed special characters (e.g., '-_.')
    
    Returns:
        str: Cleaned text
    
    Example:
        >>> remove_special_characters("Test@#$String!")
        'TestString'
        
        >>> remove_special_characters("Patient-Name_001", allowed='-_')
        'Patient-Name_001'
    """
    # Build allowed character set
    allowed_chars = string.ascii_letters + string.digits + ' ' + allowed
    
    # Filter characters
    cleaned = ''.join(c for c in text if c in allowed_chars)
    
    return cleaned


# ============================================================================
# NUMERIC VALIDATION
# ============================================================================
def validate_integer(value: str, min_value: Optional[int] = None,
                     max_value: Optional[int] = None,
                     field_name: str = "Value") -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate and parse integer value.
    
    Args:
        value: String value to validate
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        field_name: Name of field for error messages
    
    Returns:
        tuple: (is_valid, error_message, parsed_value)
               parsed_value is None if invalid
    
    Example:
        >>> valid, error, num = validate_integer("42", min_value=0, max_value=100)
        >>> print(f"Valid: {valid}, Value: {num}")
        Valid: True, Value: 42
        
        >>> valid, error, num = validate_integer("abc")
        >>> print(error)
        Value must be a valid integer
    """
    try:
        num = int(value)
        
        if min_value is not None and num < min_value:
            return False, f"{field_name} must be at least {min_value}", None
        
        if max_value is not None and num > max_value:
            return False, f"{field_name} cannot exceed {max_value}", None
        
        return True, None, num
    
    except ValueError:
        return False, f"{field_name} must be a valid integer", None


# ============================================================================
# EXPORT
# ============================================================================
__all__ = [
    # Name validation
    'validate_patient_name',
    'validate_procedure_name',
    'validate_surgeon_name',
    'validate_notes',
    'validate_tag',
    
    # Filename validation
    'validate_filename',
    'sanitize_filename',
    
    # General validation
    'validate_string_length',
    'validate_not_empty',
    'validate_pattern',
    
    # Sanitization
    'sanitize_string',
    'remove_special_characters',
    
    # Numeric
    'validate_integer',
]
