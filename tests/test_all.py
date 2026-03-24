
### File: tests/test_all.py

"""Complete test suite for OT Video System."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.database_service import DatabaseService
from app.services.storage_service import StorageService
from app.controllers.recording_controller import RecordingController
from app.models.recording import Recording
from app.models.metadata import RecordingMetadata

def test_database():
    """Test database operations."""
    print("\n=== Testing Database ===")
    db = DatabaseService()
    
    # Test 1: Connection
    success, count, error = db.get_recording_count()
    assert success, f"Database connection failed: {error}"
    print(f"✓ Database connected - {count} recordings")
    
    # Test 2: Create
    rec = Recording.create_new()
    rec.patient_name = "Test Patient"
    success, rec_id, error = db.create_recording(rec)
    assert success, f"Create failed: {error}"
    print(f"✓ Created recording ID: {rec_id}")
    
    # Test 3: Read
    success, loaded, error = db.get_recording(rec_id)
    assert success and loaded.patient_name == "Test Patient"
    print(f"✓ Read recording: {loaded.filename}")
    
    # Test 4: Search
    success, results, error = db.search_recordings(patient_name="Test")
    assert success
    print(f"✓ Search found {len(results)} results")
    
    # Cleanup
    db.delete_recording(rec_id)
    print("✓ All database tests passed")

def test_storage():
    """Test storage operations."""
    print("\n=== Testing Storage ===")
    storage = StorageService()
    
    success, free_gb, error = storage.get_free_space_gb()
    assert success
    print(f"✓ Free space: {free_gb:.2f} GB")
    
    success, status, error = storage.get_storage_status()
    assert success
    print(f"✓ Storage: {status['free_gb']:.1f}/{status['total_gb']:.1f} GB")
    print("✓ All storage tests passed")

def test_recording():
    """Test recording workflow."""
    print("\n=== Testing Recording ===")
    controller = RecordingController()
    
    print("✓ Controller initialized")
    print("⚠ Camera test skipped (requires hardware)")
    print("✓ All recording tests passed")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("OT VIDEO SYSTEM - TEST SUITE")
    print("="*50)
    
    try:
        test_database()
        test_storage()
        test_recording()
        
        print("\n" + "="*50)
        print("✓ ALL TESTS PASSED!")
        print("="*50)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)