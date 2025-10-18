"""Logging configuration."""
import sys
from pathlib import Path
from loguru import logger
from src.config import config


def setup_logger():
    """Configure loguru logger."""
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.LOG_LEVEL,
        colorize=True,
    )
    
    # File handler
    logger.add(
        config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.LOG_LEVEL,
        rotation="100 MB",
        retention="30 days",
        compression="zip",
    )
    
    return logger


# Initialize logger
log = setup_logger()

