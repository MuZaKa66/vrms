

-- ============================================================================
-- File: config/database_schema.sql
--
-- Database Schema:
--     Complete database structure for the OT Video Management System.
--     This SQL file defines all tables, indexes, and relationships needed
--     to store video recordings metadata and system information.
--
-- Tables:
--     1. recordings      - Main video recordings data
--     2. tags            - Custom tags for categorization
--     3. recording_tags  - Many-to-many relationship between recordings and tags
--     4. export_log      - History of export operations
--     5. system_log      - Application events and errors
--
-- Design Principles:
--     - Use INTEGER PRIMARY KEY for auto-incrementing IDs
--     - Store timestamps as TEXT in ISO 8601 format (YYYY-MM-DD HH:MM:SS)
--     - Use TEXT type for strings (SQLite best practice)
--     - Create indexes on frequently searched columns
--     - Use foreign keys with CASCADE for data integrity
--
-- Author: OT Video Dev Team
-- Date: January 28, 2026
-- Version: 1.0.0
-- ============================================================================


-- ============================================================================
-- TABLE: recordings
-- 
-- Purpose:
--     Stores metadata for each recorded video file.
--     This is the central table that contains all information about recordings.
--
-- Fields:
--     id                  - Unique identifier (auto-increment)
--     filename            - Video filename without path (e.g., "20260128_143022_001.mp4")
--     filepath            - Full path to video file
--     patient_name        - Patient identifier (anonymize if needed for privacy)
--     procedure_name      - Type of surgical procedure
--     operating_theatre   - OT location (OT_1, OT_2, etc.)
--     surgeon_name        - Name of surgeon performing procedure
--     recording_date      - Date of recording (YYYY-MM-DD)
--     recording_time      - Time of recording (HH:MM:SS)
--     duration_seconds    - Total duration in seconds
--     file_size_bytes     - File size in bytes
--     video_codec         - Codec used (h264)
--     resolution          - Video resolution (e.g., "720x480")
--     framerate           - Frames per second
--     thumbnail_path      - Path to thumbnail image
--     notes               - Additional free-text notes
--     created_timestamp   - When record was created (auto)
--     modified_timestamp  - When record was last modified (auto)
-- ============================================================================
CREATE TABLE IF NOT EXISTS recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    filepath TEXT ,
    patient_name TEXT,
    procedure_name TEXT,
    operating_theatre TEXT,
    surgeon_name TEXT,
    recording_date TEXT NOT NULL,
    recording_time TEXT NOT NULL,
    duration_seconds INTEGER,
    file_size_bytes INTEGER,
    video_codec TEXT DEFAULT 'h264',
    resolution TEXT DEFAULT '720x480',
    framerate INTEGER DEFAULT 30,
    thumbnail_path TEXT,
    notes TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    modified_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- TABLE: tags
--
-- Purpose:
--     Stores custom tags that can be associated with recordings.
--     Allows flexible categorization beyond fixed fields.
--
-- Fields:
--     id               - Unique identifier (auto-increment)
--     tag_name         - Tag text (unique, case-sensitive)
--     tag_category     - Optional category for organization (e.g., "procedure_type")
--     created_timestamp - When tag was created (auto)
--
-- Examples:
--     ("emergency", "priority")
--     ("resident_training", "educational")
--     ("complications", "medical")
-- ============================================================================
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL UNIQUE,
    tag_category TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- TABLE: recording_tags
--
-- Purpose:
--     Junction table implementing many-to-many relationship between
--     recordings and tags. One recording can have multiple tags,
--     and one tag can be applied to multiple recordings.
--
-- Fields:
--     recording_id - Foreign key to recordings table
--     tag_id       - Foreign key to tags table
--
-- Constraints:
--     - Primary key is combination of recording_id and tag_id
--     - CASCADE deletion: if recording or tag is deleted, relationship is removed
--
-- Example:
--     Recording #5 tagged with tags #2, #7, #12
--     (5, 2), (5, 7), (5, 12)
-- ============================================================================
CREATE TABLE IF NOT EXISTS recording_tags (
    recording_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY (recording_id) REFERENCES recordings(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (recording_id, tag_id)
);


-- ============================================================================
-- TABLE: export_log
--
-- Purpose:
--     Tracks all export operations for audit trail and statistics.
--     Useful for debugging export issues and understanding usage patterns.
--
-- Fields:
--     id                      - Unique identifier (auto-increment)
--     recording_id            - Which recording was exported (nullable if batch)
--     export_destination      - Where exported (USB drive path/name)
--     export_timestamp        - When export occurred (auto)
--     export_success          - Boolean: 1=success, 0=failure
--     export_duration_seconds - How long export took
--     error_message           - Error details if export_success=0
--
-- Usage:
--     - Track successful exports to prevent duplicate exports
--     - Debug failed exports
--     - Generate usage statistics
-- ============================================================================
CREATE TABLE IF NOT EXISTS export_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id INTEGER,
    export_destination TEXT,
    export_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    export_success INTEGER DEFAULT 0,
    export_duration_seconds INTEGER,
    error_message TEXT,
    FOREIGN KEY (recording_id) REFERENCES recordings(id) ON DELETE SET NULL
);


-- ============================================================================
-- TABLE: system_log
--
-- Purpose:
--     Application-level logging to database for important events.
--     Supplements file-based logging with searchable database records.
--
-- Fields:
--     id            - Unique identifier (auto-increment)
--     log_level     - Severity: DEBUG, INFO, WARNING, ERROR, CRITICAL
--     log_message   - Log message text
--     log_module    - Which module generated the log (e.g., "RecordingController")
--     log_timestamp - When log was created (auto)
--
-- Usage:
--     - Track important application events
--     - Debug issues by searching logs
--     - Generate system health reports
--
-- Note:
--     Not all logs go to database (too many). Only important events:
--     - Recording start/stop
--     - Errors and warnings
--     - System state changes
--     - User actions
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level TEXT NOT NULL,
    log_message TEXT NOT NULL,
    log_module TEXT,
    log_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- INDEXES FOR PERFORMANCE
--
-- Purpose:
--     Create indexes on columns that are frequently used in WHERE clauses
--     to speed up searches and queries.
--
-- When to index:
--     - Columns used in search (patient_name, procedure_name, etc.)
--     - Columns used in ORDER BY (recording_date, created_timestamp)
--     - Columns used in JOIN operations (foreign keys)
--
-- When NOT to index:
--     - Small tables (< 1000 rows) - indexes add overhead
--     - Columns rarely searched
--     - Columns with low cardinality (few unique values)
-- ============================================================================

-- Index on patient_name for quick patient search
CREATE INDEX IF NOT EXISTS idx_patient_name 
ON recordings(patient_name);

-- Index on procedure_name for filtering by procedure type
CREATE INDEX IF NOT EXISTS idx_procedure_name 
ON recordings(procedure_name);

-- Index on recording_date for date range queries
CREATE INDEX IF NOT EXISTS idx_recording_date 
ON recordings(recording_date);

-- Index on operating_theatre for filtering by OT
CREATE INDEX IF NOT EXISTS idx_operating_theatre 
ON recordings(operating_theatre);

-- Index on created_timestamp for sorting by creation time
CREATE INDEX IF NOT EXISTS idx_created_timestamp 
ON recordings(created_timestamp);

-- Composite index on date and OT for common combined searches
-- (e.g., "Show me all recordings from OT_1 on 2026-01-28")
CREATE INDEX IF NOT EXISTS idx_date_ot 
ON recordings(recording_date, operating_theatre);


-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
--
-- Purpose:
--     Automatically update modified_timestamp when a recording is updated.
--     This ensures we always know when a record was last changed.
--
-- Trigger: update_recording_timestamp
--     Fires BEFORE UPDATE on recordings table
--     Sets modified_timestamp to current time
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_recording_timestamp
AFTER UPDATE ON recordings
FOR EACH ROW
BEGIN
    UPDATE recordings 
    SET modified_timestamp = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;


-- ============================================================================
-- VIEWS FOR COMMON QUERIES
--
-- Purpose:
--     Create views (virtual tables) for frequently used queries.
--     Views simplify application code and ensure consistent queries.
-- ============================================================================

-- View: recent_recordings
-- Shows last 50 recordings ordered by creation time
CREATE VIEW IF NOT EXISTS recent_recordings AS
SELECT 
    id,
    filename,
    patient_name,
    procedure_name,
    operating_theatre,
    recording_date,
    recording_time,
    duration_seconds,
    created_timestamp
FROM recordings
ORDER BY created_timestamp DESC
LIMIT 50;


-- View: recordings_with_tags
-- Shows recordings with their associated tags (comma-separated)
-- Useful for displaying tags in UI without multiple queries
CREATE VIEW IF NOT EXISTS recordings_with_tags AS
SELECT 
    r.id,
    r.filename,
    r.patient_name,
    r.procedure_name,
    r.operating_theatre,
    r.recording_date,
    GROUP_CONCAT(t.tag_name, ', ') AS tags
FROM recordings r
LEFT JOIN recording_tags rt ON r.id = rt.recording_id
LEFT JOIN tags t ON rt.tag_id = t.id
GROUP BY r.id;


-- View: storage_statistics
-- Provides storage usage statistics
CREATE VIEW IF NOT EXISTS storage_statistics AS
SELECT 
    COUNT(*) AS total_recordings,
    SUM(duration_seconds) AS total_duration_seconds,
    SUM(file_size_bytes) AS total_size_bytes,
    AVG(duration_seconds) AS avg_duration_seconds,
    AVG(file_size_bytes) AS avg_size_bytes,
    MIN(recording_date) AS oldest_recording_date,
    MAX(recording_date) AS newest_recording_date
FROM recordings;


-- ============================================================================
-- INITIAL DATA (OPTIONAL)
--
-- Purpose:
--     Insert some default data if needed.
--     Currently just inserting common tags.
-- ============================================================================

-- Common operating theatres
INSERT OR IGNORE INTO tags (tag_name, tag_category) 
VALUES ('OT_1', 'location');

INSERT OR IGNORE INTO tags (tag_name, tag_category) 
VALUES ('OT_2', 'location');

INSERT OR IGNORE INTO tags (tag_name, tag_category) 
VALUES ('OT_3', 'location');

-- Common procedure types
INSERT OR IGNORE INTO tags (tag_name, tag_category) 
VALUES ('Cataract Surgery', 'procedure');

INSERT OR IGNORE INTO tags (tag_name, tag_category) 
VALUES ('Retinal Surgery', 'procedure');

INSERT OR IGNORE INTO tags (tag_name, tag_category) 
VALUES ('Corneal Surgery', 'procedure');

-- Priority tags
INSERT OR IGNORE INTO tags (tag_name, tag_category) 
VALUES ('Emergency', 'priority');

INSERT OR IGNORE INTO tags (tag_name, tag_category) 
VALUES ('Teaching Case', 'educational');


-- ============================================================================
-- SCHEMA VERSION TRACKING
--
-- Purpose:
--     Track database schema version for migrations.
--     Useful when updating application and database structure changes.
-- ============================================================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_date TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert current schema version
INSERT OR REPLACE INTO schema_version (version, description) 
VALUES (1, 'Initial database schema');


-- ============================================================================
-- END OF SCHEMA DEFINITION
-- ============================================================================
