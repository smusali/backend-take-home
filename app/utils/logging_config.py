"""
Logging configuration for the Lead Management API.

Provides structured logging with file rotation, environment-specific levels,
and console output for development and production environments.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.core.config import get_settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that adds structured information to log records.
    
    Enhances log messages with consistent formatting and additional context
    like timestamp, log level, module name, and function name.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with structured information.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        # Add custom fields to the record
        record.module_name = record.module
        record.func_name = record.funcName
        
        # Format the message using the parent formatter
        formatted = super().format(record)
        
        return formatted


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: str = "logs",
    log_file: str = "app.log"
) -> logging.Logger:
    """
    Configure application-wide logging with file and console handlers.
    
    Sets up structured logging with:
    - Console handler for real-time output
    - Rotating file handler for persistent logs
    - Environment-specific log levels
    - Consistent formatting across handlers
    
    Args:
        log_level: Override log level (defaults to settings.LOG_LEVEL)
        log_dir: Directory for log files (default: "logs")
        log_file: Name of the log file (default: "app.log")
        
    Returns:
        Configured root logger
        
    Example:
        >>> logger = setup_logging(log_level="INFO")
        >>> logger.info("Application started")
    """
    settings = get_settings()
    
    # Determine log level
    level = log_level or settings.LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(module)s.%(funcName)s:%(lineno)d | %(message)s"
    )
    simple_format = "%(asctime)s | %(levelname)-8s | %(message)s"
    
    detailed_formatter = StructuredFormatter(
        detailed_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    simple_formatter = StructuredFormatter(
        simple_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (use simple format for console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation (use detailed format for files)
    file_handler = RotatingFileHandler(
        filename=log_path / log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (only logs ERROR and CRITICAL)
    error_file_handler = RotatingFileHandler(
        filename=log_path / "errors.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Suppress noisy third-party loggers in production
    if settings.ENVIRONMENT == "production":
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module (typically __name__)
        
    Returns:
        Logger instance for the module
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request")
    """
    return logging.getLogger(name)


def log_lead_creation(logger: logging.Logger, lead_id: str, email: str) -> None:
    """
    Log lead creation event with structured information.
    
    Args:
        logger: Logger instance
        lead_id: UUID of the created lead
        email: Email address of the lead
    """
    logger.info(f"Lead created | ID: {lead_id} | Email: {email}")


def log_lead_status_update(
    logger: logging.Logger,
    lead_id: str,
    old_status: str,
    new_status: str,
    user: str
) -> None:
    """
    Log lead status update event.
    
    Args:
        logger: Logger instance
        lead_id: UUID of the lead
        old_status: Previous status
        new_status: New status
        user: Username who performed the update
    """
    logger.info(
        f"Lead status updated | ID: {lead_id} | "
        f"{old_status} -> {new_status} | User: {user}"
    )


def log_authentication_attempt(
    logger: logging.Logger,
    username: str,
    success: bool,
    ip_address: Optional[str] = None
) -> None:
    """
    Log authentication attempt.
    
    Args:
        logger: Logger instance
        username: Username attempting to authenticate
        success: Whether authentication succeeded
        ip_address: Optional IP address of the client
    """
    status = "SUCCESS" if success else "FAILED"
    ip_info = f" | IP: {ip_address}" if ip_address else ""
    logger.info(f"Authentication {status} | Username: {username}{ip_info}")


def log_email_sent(
    logger: logging.Logger,
    recipient: str,
    subject: str,
    success: bool
) -> None:
    """
    Log email sending event.
    
    Args:
        logger: Logger instance
        recipient: Email recipient
        subject: Email subject
        success: Whether email was sent successfully
    """
    status = "sent" if success else "failed"
    logger.info(f"Email {status} | To: {recipient} | Subject: {subject}")


def log_file_upload(
    logger: logging.Logger,
    filename: str,
    file_size: int,
    lead_id: str
) -> None:
    """
    Log file upload event.
    
    Args:
        logger: Logger instance
        filename: Name of the uploaded file
        file_size: Size in bytes
        lead_id: Associated lead ID
    """
    size_mb = file_size / (1024 * 1024)
    logger.info(
        f"File uploaded | Name: {filename} | "
        f"Size: {size_mb:.2f}MB | Lead ID: {lead_id}"
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[str] = None,
    include_stack: bool = True
) -> None:
    """
    Log error with optional stack trace.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Optional context information
        include_stack: Whether to include stack trace
    """
    error_type = error.__class__.__name__
    error_msg = str(error)
    
    if context:
        log_message = f"Error in {context} | {error_type}: {error_msg}"
    else:
        log_message = f"{error_type}: {error_msg}"
    
    if include_stack:
        logger.error(log_message, exc_info=True)
    else:
        logger.error(log_message)


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user: Optional[str] = None
) -> None:
    """
    Log HTTP request with timing information.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user: Optional authenticated user
    """
    user_info = f" | User: {user}" if user else ""
    logger.info(
        f"{method} {path} | Status: {status_code} | "
        f"Duration: {duration_ms:.2f}ms{user_info}"
    )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    record_id: Optional[str] = None,
    duration_ms: Optional[float] = None
) -> None:
    """
    Log database operation.
    
    Args:
        logger: Logger instance
        operation: Type of operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        record_id: Optional record ID
        duration_ms: Optional operation duration
    """
    id_info = f" | ID: {record_id}" if record_id else ""
    duration_info = f" | Duration: {duration_ms:.2f}ms" if duration_ms else ""
    logger.debug(f"DB {operation} | Table: {table}{id_info}{duration_info}")


def log_startup(logger: logging.Logger, environment: str, debug: bool) -> None:
    """
    Log application startup information.
    
    Args:
        logger: Logger instance
        environment: Environment name (development, production, etc.)
        debug: Whether debug mode is enabled
    """
    logger.info("=" * 70)
    logger.info("Lead Management API Starting")
    logger.info(f"Environment: {environment}")
    logger.info(f"Debug Mode: {debug}")
    logger.info("=" * 70)


def log_shutdown(logger: logging.Logger) -> None:
    """
    Log application shutdown.
    
    Args:
        logger: Logger instance
    """
    logger.info("=" * 70)
    logger.info("Lead Management API Shutting Down")
    logger.info("=" * 70)


__all__ = [
    "setup_logging",
    "get_logger",
    "log_lead_creation",
    "log_lead_status_update",
    "log_authentication_attempt",
    "log_email_sent",
    "log_file_upload",
    "log_error",
    "log_request",
    "log_database_operation",
    "log_startup",
    "log_shutdown",
]
