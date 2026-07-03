import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder configuration
    # STORAGE_FOLDER = os.path.join(BASE_DIR, 'storage')
    STORAGE_FOLDER = os.path.join('E:\\', 'Fotos Quadros', '2026')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max limit per request, optional but good
