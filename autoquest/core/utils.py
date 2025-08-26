"""
Utility functions for AutoQuest
"""

import os
import re
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import mimetypes
from urllib.parse import urlparse


def generate_id(prefix: str = "aq") -> str:
    """
    Generate a unique identifier
    
    Args:
        prefix: Prefix for the ID
        
    Returns:
        Unique identifier string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_part = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_part}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename


def validate_file_type(file_path: Union[str, Path], allowed_types: List[str]) -> bool:
    """
    Validate file type against allowed types
    
    Args:
        file_path: Path to the file
        allowed_types: List of allowed file extensions
        
    Returns:
        True if file type is allowed
    """
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    return file_extension in allowed_types


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get comprehensive file information
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = file_path.stat()
    
    return {
        "name": file_path.name,
        "stem": file_path.stem,
        "suffix": file_path.suffix,
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime),
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "accessed": datetime.fromtimestamp(stat.st_atime),
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "mime_type": mimetypes.guess_type(str(file_path))[0]
    }


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calculate file hash
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        File hash string
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp to string
    
    Args:
        timestamp: Datetime object
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse timestamp string to datetime
    
    Args:
        timestamp_str: Timestamp string
        format_str: Format string
        
    Returns:
        Datetime object
    """
    return datetime.strptime(timestamp_str, format_str)


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score between 0 and 1
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same length")
    
    if not vec1 or not vec2:
        return 0.0
    
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Calculate magnitudes
    mag1 = sum(a * a for a in vec1) ** 0.5
    mag2 = sum(b * b for b in vec2) ** 0.5
    
    # Avoid division by zero
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


def chunk_text(text: str, chunk_size: int, overlap: int = 0) -> List[str]:
    """
    Split text into chunks with optional overlap
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    if overlap >= chunk_size:
        raise ValueError("Overlap must be less than chunk size")
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Normalize unicode
    text = text.encode('utf-8', errors='ignore').decode('utf-8')
    return text


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text
    
    Args:
        text: Text to extract URLs from
        
    Returns:
        List of URLs found in text
    """
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    return re.findall(url_pattern, text)


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary
    
    Args:
        dictionary: Dictionary to get value from
        key: Key to look for
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    return dictionary.get(key, default)


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(dictionary: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary
    
    Args:
        dictionary: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    
    for key, value in dictionary.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    
    return dict(items)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    return file_path.stat().st_size / (1024 * 1024)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Retry function with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    import time
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt == max_retries:
                raise last_exception
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)
            time.sleep(delay)
    
    raise last_exception
