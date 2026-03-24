"""
File: main.py

Module Description:
    OT Video Management System - Main Application Entry Point
    
    Professional medical video recording system for operating theatres.
    
    Features:
    - Zero-friction video recording
    - Optional metadata (patient, procedure, OT, consultant)
    - Video library with search
    - USB export functionality
    - Offline voice commands
    - Air-gapped security (HIPAA/GDPR compliant)
    
    Hardware:
    - Raspberry Pi 4 (4GB RAM)
    - USB video capture device (CVBS)
    - 7" touchscreen display
    - USB microphone (optional)
    - 256GB SSD storage

Author: OT Video Dev Team
Date: March 24, 2026
Version: 1.1.0
Changelog:
    - v1.1.0: Removed splash screen and disclaimer for faster boot
    - v1.0.0: Initial release
"""

import sys
import signal
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtCore import Qt

# Set up paths
sys.path.insert(0, str(Path(__file__).parent))

from app.gui.main_window import MainWindow
from app.services.storage_service import StorageService
from app.services.database_service import DatabaseService
from config.init_database import initialize_database
from app.utils.logger import AppLogger

# Initialize logger
logger = AppLogger("Main")


def initialize_system():
    """
    Initialize system on startup.
    
    Steps:
    1. Initialize database
    2. Check storage
    3. Verify directories
    4. Log system info
    
    Returns:
        tuple: (success, error_message)
    """
    logger.info("=" * 60)
    logger.info("VRMS SYSTEM STARTING")
    logger.info("=" * 60)
    
    # Log system information
    logger.log_system_info()
    
    # Step 1: Initialize database
    logger.info("Initializing database...")
    try:
        initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        error_msg = f"Database initialization failed: {e}"
        logger.error(error_msg)
        return False, error_msg
    
    # Step 2: Verify database connection
    logger.info("Verifying database connection...")
    db = DatabaseService()
    success, count, error = db.get_recording_count()
    if not success:
        return False, f"Database connection failed: {error}"
    logger.info(f"Database OK - {count} recordings found")
    
    # Step 3: Check storage
    logger.info("Checking storage...")
    storage = StorageService()
    success, error = storage.ensure_directories()
    if not success:
        return False, f"Storage initialization failed: {error}"
    
    success, status, error = storage.get_storage_status()
    if success:
        logger.info(
            f"Storage OK - {status['free_gb']:.1f} GB free of "
            f"{status['total_gb']:.1f} GB"
        )
        
        if status['is_critical']:
            logger.warning("WARNING: Storage critically low!")
        elif status['is_low']:
            logger.warning("WARNING: Storage running low")
    else:
        logger.warning(f"Storage check failed: {error}")
    
    # Step 4: Clean temp directory
    logger.info("Cleaning temporary files...")
    success, count, error = storage.clean_temp_directory()
    if success:
        logger.info(f"Cleaned {count} temporary files")
    
    logger.info("System initialization complete")
    logger.info("=" * 60)
    
    return True, None


def setup_signal_handlers():
    """Setup signal handlers for clean shutdown."""
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        logger.info("Cleaning up...")
        QApplication.quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """
    Main application entry point.
    
    STARTUP SEQUENCE:
    1. Initialize Qt application
    2. Initialize system (database, storage, etc.)
    3. Show main window directly (no splash/disclaimer for faster boot)
    """
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("VRMS - Video Recording Management System")
    app.setOrganizationName("Lahore General Hospital")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Initialize system
    success, error = initialize_system()
    
    if not success:
        # Show error dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Initialization Error")
        msg.setText("System initialization failed")
        msg.setInformativeText(error)
        msg.setDetailedText(
            "Please check:\n"
            "1. Storage device is connected\n"
            "2. Database is accessible\n"
            "3. Permissions are correct\n\n"
            "Check logs for more details."
        )
        msg.exec_()
        
        logger.error("Application startup failed")
        return 1

        # ── Storage Health Check ──
    logger.info("Checking storage health...")
    from config.app_config import check_storage_health, detect_boot_device
    from pathlib import Path
    
    # Get current storage path
    from config.app_config import VIDEO_STORAGE_PATH
    storage_health = check_storage_health(VIDEO_STORAGE_PATH)
    
    if not storage_health['accessible'] or not storage_health['writable']:
        logger.error(f"Storage issue: {storage_health['error']}")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Storage Error")
        msg.setText("Storage device is not accessible")
        msg.setInformativeText(
            f"Cannot access: {VIDEO_STORAGE_PATH}\n\n"
            f"Error: {storage_health['error']}\n\n"
            "Please contact manufacturer for replacement."
        )
        msg.exec_()
        return 1
    
    # Check boot device
    boot_info = detect_boot_device()
    if boot_info['is_fallback']:
        logger.warning(f"Running on fallback device: {boot_info['boot_device']}")
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Storage Warning")
        msg.setText("Running on fallback storage")
        msg.setInformativeText(
            f"System is running from {boot_info['boot_device']}.\n\n"
            "Primary storage device may have failed.\n\n"
            "Please contact manufacturer for replacement."
        )
        msg.exec_()
        # Continue running - non-blocking warning




    # ── Splash Screen REMOVED for faster boot ──
    # Original splash screen code commented out:
    # logger.info("Showing splash screen...")
    # from app.gui.dialogs import SplashScreen
    # splash = SplashScreen()
    # splash.exec_()
    
    # ── Disclaimer Screen REMOVED for faster boot ──
    # Original disclaimer code commented out:
    # from app.gui.recording.design_constants import is_disclaimer_accepted
    # from app.gui.dialogs import DisclaimerDialog
    # 
    # if not is_disclaimer_accepted():
    #     logger.info("First launch - showing disclaimer...")
    #     disclaimer = DisclaimerDialog()
    #     result = disclaimer.exec_()
    #     
    #     if result != QDialog.Accepted:
    #         logger.warning("Disclaimer rejected - exiting")
    #         QMessageBox.information(
    #             None, "Exit",
    #             "You must accept the terms to use this application."
    #         )
    #         return 1
    #     
    #     logger.info("Disclaimer accepted")
    # else:
    #     logger.info("Disclaimer previously accepted")
    
    # ── Create and Show Main Window ──
    logger.info("Creating main window...")
    window = MainWindow()
    
    # Fullscreen for production (uncomment for deployment)
    # window.showFullScreen()
    
    # Normal window for development
    window.show()
    
    logger.info("Application started successfully")
    logger.info("Ready for operation")
    
    # Run application
    exit_code = app.exec_()
    
    # Cleanup on exit
    logger.info("Application shutting down...")
    logger.info("Exit code: {}".format(exit_code))
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())