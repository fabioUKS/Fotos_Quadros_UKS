import os
import tempfile

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder configuration
    # STORAGE_FOLDER = os.path.join(BASE_DIR, 'storage')
    HD_BASE_PATH = 'E:\\Fotos Quadros'
    HD_ACTIVE_YEAR = '2026'
    STORAGE_FOLDER = os.path.join(HD_BASE_PATH, HD_ACTIVE_YEAR)
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1024 MB max limit per request, optional but good
    
    # Authomatic synchronization 
    AUTO_SYNC_ENABLED = True  #  Enable/disable scheduler
    AUTO_SYNC_INTERVAL_HOURS = 24  # Synchronization frequency
    SYNC_ON_STARTUP = True  # Synchronize when starting the server
    SYNC_BATCH_SIZE = 100  # Process in batches

    # Synchronization performance
    SYNC_USE_THREADING = True
    SYNC_THREAD_POOL_SIZE = 4  # Number of threads runing on parallel
    SYNC_CHUNK_SIZE = 50
    
    # Synchronization logging
    SYNC_LOG_FILE = os.path.join(BASE_DIR, 'logs', 'sync.log')
    SYNC_LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
    KEEP_SYNC_LOGS_DAYS = 30
    
    # Temporary directory
    TEMP_FOLDER = 'temp'
    tempfile.tempdir = os.path.join(STORAGE_FOLDER, TEMP_FOLDER)
    os.makedirs(TEMP_FOLDER, exist_ok=True)