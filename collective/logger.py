import logging
import json
import os

def _setup_logger(name='collective_logger', log_file='logs/collective_time.json'):
    """Internal function to set up and configure logger"""
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Check if logger already has handlers to avoid duplicate handlers
    if not logger.handlers:
        # Create file handler
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Initialize logger when module is imported
logger = _setup_logger() 