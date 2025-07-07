"""
X-Trace-ID Middleware for End-to-End Traceability
Implements request tracing across the entire system
"""

from uuid import uuid4
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import structlog
import time
from typing import Callable, Optional

# Configure structured logging for trace support
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

class TraceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle X-Trace-ID propagation
    Ensures every request has a unique trace ID for end-to-end tracking
    """
    
    def __init__(self, app, header_name: str = "X-Trace-ID"):
        super().__init__(app)
        self.header_name = header_name
        self.logger = structlog.get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with trace ID propagation"""
        
        # Generate or extract trace ID
        trace_id = request.headers.get(self.header_name, str(uuid4()))
        
        # Store trace ID in request state for easy access
        request.state.trace_id = trace_id
        
        # Add trace ID to logging context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        
        # Record request start time for performance metrics
        start_time = time.time()
        
        # Log incoming request
        self.logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            trace_id=trace_id,
            client_ip=request.client.host if request.client else "unknown"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Add trace ID to response headers
            response.headers[self.header_name] = trace_id
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            # Log successful response
            self.logger.info(
                "Request completed",
                status_code=response.status_code,
                duration=f"{duration:.3f}s",
                trace_id=trace_id
            )
            
            return response
            
        except Exception as e:
            # Calculate error duration
            duration = time.time() - start_time
            
            # Log error with trace ID
            self.logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                duration=f"{duration:.3f}s",
                trace_id=trace_id
            )
            
            # Re-raise the exception
            raise
        
        finally:
            # Clean up context variables
            structlog.contextvars.clear_contextvars()

# Utility functions for routes
def get_trace_id(request: Request) -> str:
    """Get trace ID from request state"""
    return getattr(request.state, 'trace_id', 'unknown')

def add_trace_to_payload(request: Request, payload: dict) -> dict:
    """Add trace ID to any payload/data structure"""
    if isinstance(payload, dict):
        payload['trace_id'] = get_trace_id(request)
    return payload

def create_traced_logger(request: Request, name: str = __name__):
    """Create a logger with trace context"""
    logger = structlog.get_logger(name)
    trace_id = get_trace_id(request)
    return logger.bind(trace_id=trace_id)

# Database operation helpers
class TracedDatabaseOperation:
    """Helper class for database operations with trace propagation"""
    
    def __init__(self, request: Request):
        self.trace_id = get_trace_id(request)
        self.logger = structlog.get_logger(__name__).bind(trace_id=self.trace_id)
    
    def add_trace_to_insert(self, data: dict) -> dict:
        """Add trace_id to database insert operations"""
        if isinstance(data, dict):
            data['trace_id'] = self.trace_id
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    item['trace_id'] = self.trace_id
        return data
    
    def log_operation(self, operation: str, table: str, details: Optional[dict] = None):
        """Log database operation with trace context"""
        self.logger.info(
            f"Database {operation}",
            table=table,
            trace_id=self.trace_id,
            **(details or {})
        )

# Performance monitoring helpers
class TracePerformanceMonitor:
    """Monitor performance metrics with trace correlation"""
    
    def __init__(self, request: Request):
        self.trace_id = get_trace_id(request)
        self.logger = structlog.get_logger(__name__).bind(trace_id=self.trace_id)
        self.start_time = time.time()
    
    def checkpoint(self, operation: str, **kwargs):
        """Record performance checkpoint"""
        duration = time.time() - self.start_time
        self.logger.info(
            f"Performance checkpoint: {operation}",
            duration=f"{duration:.3f}s",
            trace_id=self.trace_id,
            **kwargs
        )
    
    def end(self, operation: str, **kwargs):
        """Record operation completion"""
        total_duration = time.time() - self.start_time
        self.logger.info(
            f"Operation completed: {operation}",
            total_duration=f"{total_duration:.3f}s",
            trace_id=self.trace_id,
            **kwargs
        )

# Integration with existing logging
class TraceAwareHandler(logging.Handler):
    """Logging handler that includes trace context"""
    
    def emit(self, record):
        # Get trace ID from context if available
        trace_id = structlog.contextvars.get_contextvars().get('trace_id', 'no-trace')
        
        # Add trace ID to log record
        record.trace_id = trace_id
        
        # Use structured logging
        logger = structlog.get_logger(record.name)
        
        level_method = getattr(logger, record.levelname.lower(), logger.info)
        level_method(
            record.getMessage(),
            trace_id=trace_id,
            filename=record.filename,
            lineno=record.lineno,
            funcName=record.funcName
        )

def install_trace_aware_logging():
    """Install trace-aware logging for the entire application"""
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Add trace-aware handler
    handler = TraceAwareHandler()
    handler.setLevel(logging.DEBUG)
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)

# Export main components
__all__ = [
    'TraceMiddleware',
    'get_trace_id',
    'add_trace_to_payload', 
    'create_traced_logger',
    'TracedDatabaseOperation',
    'TracePerformanceMonitor',
    'install_trace_aware_logging'
]