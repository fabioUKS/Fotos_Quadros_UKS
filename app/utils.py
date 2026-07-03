import re
import unicodedata
from werkzeug.utils import secure_filename

def sanitize_directory_name(name: str) -> str:
    """
    Sanitizes a string to be used as a directory name.
    Removes accents and keeps only alphanumeric characters, spaces, and hyphens.
    """
    # Normalize accents
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    # Keep only safe characters
    name = re.sub(r'[^a-zA-Z0-9\s-]', '', name)
    # Collapse multiple spaces and strip
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def sanitize_filename(filename: str) -> str:
    """
    Uses werkzeug's secure_filename to sanitize the file name.
    """
    return secure_filename(filename)
