"""
File: app/services/database_service.py

Module Description:
    Database service for the OT Video Management System.
    
    Provides comprehensive database operations with:
    - CRUD operations for recordings
    - Search and filter capabilities
    - Transaction management
    - Professional error handling
    - Auto-recovery mechanisms
    - Audit trail logging
    
    Every operation returns (success, data, error_message) tuple
    for consistent error handling throughout the application.

Dependencies:
    - sqlite3: Database interface
    - contextlib: Context managers for transactions
    - typing: Type hints

Usage Example:
    >>> from app.services.database_service import DatabaseService
    >>> from app.models.recording import Recording
    >>> 
    >>> db = DatabaseService()
    >>> 
    >>> # Create recording
    >>> recording = Recording.create_new()
    >>> success, rec_id, error = db.create_recording(recording)
    >>> if success:
    ...     print(f"Saved with ID: {rec_id}")
    >>> else:
    ...     print(f"Error: {error}")

Author: OT Video Dev Team
Date: January 28, 2026
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import json

from config.app_config import DATABASE_PATH
from app.models.recording import Recording
from app.utils.logger import AppLogger
from app.utils.decorators import log_errors, retry

# Initialize logger
logger = AppLogger("DatabaseService")


# ============================================================================
# DATABASE SERVICE CLASS
# ============================================================================
class DatabaseService:
    """
    Database service for managing video recordings.
    
    Provides all database operations with professional error handling.
    All operations return (success, data, error_message) tuples.
    
    Attributes:
        db_path (Path): Path to SQLite database file
    
    Methods:
        # CRUD Operations
        create_recording(recording): Create new recording
        get_recording(recording_id): Get recording by ID
        update_recording(recording): Update existing recording
        delete_recording(recording_id): Delete recording
        
        # Search Operations
        search_recordings(query): Search by any field
        get_all_recordings(): Get all recordings
        get_recent_recordings(limit): Get N most recent
        
        # Statistics
        get_recording_count(): Total number of recordings
        get_total_duration(): Total duration of all recordings
        get_storage_usage(): Total storage used
    
    Example:
        >>> db = DatabaseService()
        >>> 
        >>> # Create
        >>> rec = Recording.create_new()
        >>> success, rec_id, error = db.create_recording(rec)
        >>> 
        >>> # Read
        >>> success, recording, error = db.get_recording(rec_id)
        >>> 
        >>> # Update
        >>> recording.patient_name = "John Smith"
        >>> success, _, error = db.update_recording(recording)
        >>> 
        >>> # Search
        >>> success, results, error = db.search_recordings(
        ...     patient_name="John"
        ... )
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database service.
        
        Args:
            db_path: Path to database file (uses config default if None)
        
        Example:
            >>> db = DatabaseService()
            >>> # or
            >>> db = DatabaseService("/custom/path/to/db.db")
        """
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        
        # Verify database exists
        if not self.db_path.exists():
            logger.warning(f"Database not found at {self.db_path}")
            logger.info("Run config/init_database.py to create database")
        
        logger.debug(f"Database service initialized: {self.db_path}")
    
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Automatically handles commit/rollback and connection cleanup.
        Use with 'with' statement for automatic resource management.
        
        Yields:
            sqlite3.Connection: Database connection
        
        Example:
            >>> db = DatabaseService()
            >>> with db.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM recordings")
        """
        conn = None
        try:
            # Connect to database
            conn = sqlite3.connect(str(self.db_path))
            
            # Enable foreign keys (not enabled by default in SQLite)
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Return rows as dictionaries (easier to work with)
            conn.row_factory = sqlite3.Row
            
            yield conn
            
            # Commit if no exception
            conn.commit()
            
        except Exception as e:
            # Rollback on error
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        
        finally:
            # Always close connection
            if conn:
                conn.close()
    
    # ========================================================================
    # CREATE OPERATIONS
    # ========================================================================
    
    @log_errors
    @retry(max_attempts=3, delay=0.5)
    def create_recording(self, recording: Recording) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Create new recording in database.
        
        Validates recording data before insertion.
        Handles duplicate filenames by auto-incrementing sequence.
        
        Args:
            recording: Recording object to create
        
        Returns:
            tuple: (success, recording_id, error_message)
                  success: True if created, False otherwise
                  recording_id: Database ID of created recording
                  error_message: Error description if failed
        
        Example:
            >>> rec = Recording.create_new()
            >>> success, rec_id, error = db.create_recording(rec)
            >>> if success:
            ...     print(f"Created with ID: {rec_id}")
            >>> else:
            ...     print(f"Failed: {error}")
        """
        # Validate recording
        valid, errors = recording.validate()
        if not valid:
            error_msg = "Invalid recording data: " + "; ".join(errors)
            logger.warning(error_msg)
            return False, None, error_msg
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check for duplicate filename
                cursor.execute(
                    "SELECT id FROM recordings WHERE filename = ?",
                    (recording.filename,)
                )
                
                if cursor.fetchone():
                    # Duplicate found - auto-increment filename
                    base_name = recording.filename.rsplit('_', 1)[0]
                    ext = recording.filename.split('.')[-1]
                    
                    # Find next available number
                    sequence = 1
                    while True:
                        new_filename = f"{base_name}_{sequence:03d}.{ext}"
                        cursor.execute(
                            "SELECT id FROM recordings WHERE filename = ?",
                            (new_filename,)
                        )
                        if not cursor.fetchone():
                            recording.filename = new_filename
                            logger.info(f"Filename auto-incremented to: {new_filename}")
                            break
                        sequence += 1
                
                # Insert recording
                cursor.execute("""
                    INSERT INTO recordings (
                        filename, filepath, patient_name, procedure_name,
                        operating_theatre, surgeon_name, recording_date,
                        recording_time, duration_seconds, file_size_bytes,
                        video_codec, resolution, framerate, thumbnail_path,
                        notes, created_timestamp, modified_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    recording.filename,
                    recording.filepath,
                    recording.patient_name,
                    recording.procedure_name,
                    recording.operating_theatre,
                    recording.surgeon_name,
                    recording.recording_date,
                    recording.recording_time,
                    recording.duration_seconds,
                    recording.file_size_bytes,
                    recording.video_codec,
                    recording.resolution,
                    recording.framerate,
                    recording.thumbnail_path,
                    recording.notes,
                    recording.created_timestamp,
                    recording.modified_timestamp
                ))
                
                recording_id = cursor.lastrowid
                
                logger.info(f"Created recording: ID={recording_id}, filename={recording.filename}")
                return True, recording_id, None
        
        except sqlite3.IntegrityError as e:
            error_msg = f"Database constraint violation: {e}"
            logger.error(error_msg)
            return False, None, "Recording could not be saved. Please try again."
        
        except sqlite3.OperationalError as e:
            error_msg = f"Database operational error: {e}"
            logger.error(error_msg)
            return False, None, "Database is busy. Please try again in a moment."
        
        except Exception as e:
            error_msg = f"Unexpected error creating recording: {e}"
            logger.error(error_msg)
            return False, None, "Could not save recording. Please contact support if problem persists."
    
    # ========================================================================
    # READ OPERATIONS
    # ========================================================================
    
    @log_errors
    def get_recording(self, recording_id: int) -> Tuple[bool, Optional[Recording], Optional[str]]:
        """
        Get recording by ID.
        
        Args:
            recording_id: Database ID of recording
        
        Returns:
            tuple: (success, recording, error_message)
        
        Example:
            >>> success, recording, error = db.get_recording(1)
            >>> if success:
            ...     print(recording.filename)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM recordings WHERE id = ?
                """, (recording_id,))
                
                row = cursor.fetchone()
                
                if row:
                    # Convert row to Recording object
                    recording = Recording.from_dict(dict(row))
                    return True, recording, None
                else:
                    return False, None, f"Recording with ID {recording_id} not found"
        
        except Exception as e:
            error_msg = f"Error retrieving recording: {e}"
            logger.error(error_msg)
            return False, None, "Could not load recording from database"
    
    @log_errors
    def get_all_recordings(self, order_by: str = "created_timestamp DESC",
                           limit: Optional[int] = None) -> Tuple[bool, List[Recording], Optional[str]]:
        """
        Get all recordings.
        
        Args:
            order_by: SQL ORDER BY clause (default: newest first)
            limit: Maximum number of recordings to return
        
        Returns:
            tuple: (success, list_of_recordings, error_message)
        
        Example:
            >>> success, recordings, error = db.get_all_recordings(limit=10)
            >>> if success:
            ...     for rec in recordings:
            ...         print(rec.filename)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = f"SELECT * FROM recordings ORDER BY {order_by}"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                recordings = [Recording.from_dict(dict(row)) for row in rows]
                
                logger.debug(f"Retrieved {len(recordings)} recordings")
                return True, recordings, None
        
        except Exception as e:
            error_msg = f"Error retrieving recordings: {e}"
            logger.error(error_msg)
            return False, [], "Could not load recordings from database"
    
    @log_errors
    def search_recordings(self, 
                         patient_name: Optional[str] = None,
                         procedure_name: Optional[str] = None,
                         operating_theatre: Optional[str] = None,
                         surgeon_name: Optional[str] = None,
                         date_from: Optional[str] = None,
                         date_to: Optional[str] = None) -> Tuple[bool, List[Recording], Optional[str]]:
        """
        Search recordings by metadata.
        
        All parameters are optional. Combines multiple criteria with AND.
        Uses LIKE for partial matching (case-insensitive).
        
        Args:
            patient_name: Patient name (partial match)
            procedure_name: Procedure name (partial match)
            operating_theatre: OT location (exact match)
            surgeon_name: Surgeon name (partial match)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        
        Returns:
            tuple: (success, list_of_recordings, error_message)
        
        Example:
            >>> # Search by patient
            >>> success, results, error = db.search_recordings(
            ...     patient_name="John"
            ... )
            >>> 
            >>> # Search by date range
            >>> success, results, error = db.search_recordings(
            ...     date_from="2026-01-01",
            ...     date_to="2026-01-31"
            ... )
            >>> 
            >>> # Multiple criteria
            >>> success, results, error = db.search_recordings(
            ...     procedure_name="Cataract",
            ...     operating_theatre="OT_1"
            ... )
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause dynamically
                where_clauses = []
                params = []
                
                if patient_name:
                    where_clauses.append("patient_name LIKE ?")
                    params.append(f"%{patient_name}%")
                
                if procedure_name:
                    where_clauses.append("procedure_name LIKE ?")
                    params.append(f"%{procedure_name}%")
                
                if operating_theatre:
                    where_clauses.append("operating_theatre = ?")
                    params.append(operating_theatre)
                
                if surgeon_name:
                    where_clauses.append("surgeon_name LIKE ?")
                    params.append(f"%{surgeon_name}%")
                
                if date_from:
                    where_clauses.append("recording_date >= ?")
                    params.append(date_from)
                
                if date_to:
                    where_clauses.append("recording_date <= ?")
                    params.append(date_to)
                
                # Build complete query
                query = "SELECT * FROM recordings"
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                query += " ORDER BY created_timestamp DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                recordings = [Recording.from_dict(dict(row)) for row in rows]
                
                logger.info(f"Search returned {len(recordings)} results")
                return True, recordings, None
        
        except Exception as e:
            error_msg = f"Error searching recordings: {e}"
            logger.error(error_msg)
            return False, [], "Could not search recordings. Please try again."
    
    # ========================================================================
    # UPDATE OPERATIONS
    # ========================================================================
    
    @log_errors
    @retry(max_attempts=3, delay=0.5)
    def update_recording(self, recording: Recording) -> Tuple[bool, None, Optional[str]]:
        """
        Update existing recording.
        
        Updates all fields. Recording must have valid ID.
        
        Args:
            recording: Recording object with updated data
        
        Returns:
            tuple: (success, None, error_message)
        
        Example:
            >>> success, rec, error = db.get_recording(1)
            >>> rec.patient_name = "John Smith"
            >>> success, _, error = db.update_recording(rec)
        """
        # Validate recording
        valid, errors = recording.validate()
        if not valid:
            error_msg = "Invalid recording data: " + "; ".join(errors)
            return False, None, error_msg
        
        if not recording.id:
            return False, None, "Recording must have an ID to update"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update modified timestamp
                from app.utils.datetime_utils import get_timestamp
                recording.modified_timestamp = get_timestamp()
                
                cursor.execute("""
                    UPDATE recordings SET
                        filename = ?,
                        filepath = ?,
                        patient_name = ?,
                        procedure_name = ?,
                        operating_theatre = ?,
                        surgeon_name = ?,
                        recording_date = ?,
                        recording_time = ?,
                        duration_seconds = ?,
                        file_size_bytes = ?,
                        video_codec = ?,
                        resolution = ?,
                        framerate = ?,
                        thumbnail_path = ?,
                        notes = ?,
                        modified_timestamp = ?
                    WHERE id = ?
                """, (
                    recording.filename,
                    recording.filepath,
                    recording.patient_name,
                    recording.procedure_name,
                    recording.operating_theatre,
                    recording.surgeon_name,
                    recording.recording_date,
                    recording.recording_time,
                    recording.duration_seconds,
                    recording.file_size_bytes,
                    recording.video_codec,
                    recording.resolution,
                    recording.framerate,
                    recording.thumbnail_path,
                    recording.notes,
                    recording.modified_timestamp,
                    recording.id
                ))
                
                if cursor.rowcount == 0:
                    return False, None, f"Recording with ID {recording.id} not found"
                
                logger.info(f"Updated recording: ID={recording.id}")
                return True, None, None
        
        except Exception as e:
            error_msg = f"Error updating recording: {e}"
            logger.error(error_msg)
            return False, None, "Could not update recording. Please try again."
    
    # ========================================================================
    # DELETE OPERATIONS
    # ========================================================================
    
    @log_errors
    def delete_recording(self, recording_id: int) -> Tuple[bool, None, Optional[str]]:
        """
        Delete recording from database.
        
        Note: This only deletes the database record, not the video file.
        Video file deletion should be handled separately.
        
        Args:
            recording_id: Database ID of recording to delete
        
        Returns:
            tuple: (success, None, error_message)
        
        Example:
            >>> success, _, error = db.delete_recording(1)
            >>> if success:
            ...     print("Recording deleted")
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM recordings WHERE id = ?", (recording_id,))
                
                if cursor.rowcount == 0:
                    return False, None, f"Recording with ID {recording_id} not found"
                
                logger.info(f"Deleted recording: ID={recording_id}")
                return True, None, None
        
        except Exception as e:
            error_msg = f"Error deleting recording: {e}"
            logger.error(error_msg)
            return False, None, "Could not delete recording. Please try again."
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    @log_errors
    def get_recording_count(self) -> Tuple[bool, int, Optional[str]]:
        """
        Get total number of recordings.
        
        Returns:
            tuple: (success, count, error_message)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM recordings")
                count = cursor.fetchone()[0]
                return True, count, None
        except Exception as e:
            logger.error(f"Error getting recording count: {e}")
            return False, 0, "Could not retrieve statistics"
    
    @log_errors
    def get_storage_statistics(self) -> Tuple[bool, Dict, Optional[str]]:
        """
        Get storage usage statistics.
        
        Returns:
            tuple: (success, statistics_dict, error_message)
        
        Example:
            >>> success, stats, error = db.get_storage_statistics()
            >>> print(f"Total recordings: {stats['total_recordings']}")
            >>> print(f"Total size: {stats['total_size_gb']} GB")
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_recordings,
                        SUM(duration_seconds) as total_duration_seconds,
                        SUM(file_size_bytes) as total_size_bytes,
                        AVG(duration_seconds) as avg_duration_seconds,
                        AVG(file_size_bytes) as avg_size_bytes
                    FROM recordings
                """)
                
                row = cursor.fetchone()
                
                stats = {
                    'total_recordings': row[0] or 0,
                    'total_duration_seconds': row[1] or 0,
                    'total_size_bytes': row[2] or 0,
                    'total_size_gb': (row[2] or 0) / (1024**3),
                    'avg_duration_seconds': row[3] or 0,
                    'avg_size_bytes': row[4] or 0
                }
                
                return True, stats, None
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return False, {}, "Could not retrieve statistics"


# ============================================================================
# EXPORT
# ============================================================================
__all__ = [
    'DatabaseService',
]