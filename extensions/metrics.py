"""
Prometheus metrics for monitoring application performance and usage.
"""
from flask import Blueprint, request, g
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry
from functools import wraps
import time

# Create metrics blueprint
metrics_bp = Blueprint('metrics', __name__)

# Create registry
registry = CollectorRegistry()

# Application info
app_info = Info(
    'cisco_config_generator',
    'Cisco Configuration Generator application information',
    registry=registry
)

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Configuration generation metrics
config_generated_total = Counter(
    'config_generated_total',
    'Total configurations generated',
    ['platform', 'format'],
    registry=registry
)

config_generation_duration = Histogram(
    'config_generation_duration_seconds',
    'Configuration generation duration in seconds',
    ['platform'],
    registry=registry
)

config_validation_errors = Counter(
    'config_validation_errors_total',
    'Total configuration validation errors',
    ['error_type'],
    registry=registry
)

# Authentication metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['method', 'status'],
    registry=registry
)

active_sessions = Gauge(
    'active_sessions',
    'Number of active user sessions',
    registry=registry
)

api_key_usage = Counter(
    'api_key_usage_total',
    'API key usage',
    ['key_id'],
    registry=registry
)

# Database metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation'],
    registry=registry
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    registry=registry
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint'],
    registry=registry
)

# Resource metrics
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

# History metrics
history_entries_total = Gauge(
    'history_entries_total',
    'Total history entries',
    registry=registry
)

history_size_bytes = Gauge(
    'history_size_bytes',
    'Total size of history entries in bytes',
    registry=registry
)


class MetricsMiddleware:
    """Middleware to track request metrics."""

    def __init__(self, app=None):
        """
        Initialize metrics middleware.

        Args:
            app: Flask application
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize Flask app with metrics.

        Args:
            app: Flask application
        """
        # Set application info
        app_info.info({
            'version': app.config.get('VERSION', '1.0.0'),
            'environment': app.config.get('FLASK_ENV', 'production')
        })

        # Register before and after request handlers
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    @staticmethod
    def before_request():
        """Track request start time."""
        g.start_time = time.time()

    @staticmethod
    def after_request(response):
        """Track request completion and metrics."""
        if hasattr(g, 'start_time'):
            # Calculate duration
            duration = time.time() - g.start_time

            # Get endpoint
            endpoint = request.endpoint or 'unknown'

            # Record metrics
            request_count.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()

            request_duration.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)

        return response


def track_config_generation(platform: str, format_type: str):
    """
    Track configuration generation.

    Args:
        platform: Platform type
        format_type: Output format
    """
    config_generated_total.labels(
        platform=platform,
        format=format_type
    ).inc()


def track_config_generation_time(platform: str):
    """
    Decorator to track configuration generation time.

    Args:
        platform: Platform type

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with config_generation_duration.labels(platform=platform).time():
                return func(*args, **kwargs)
        return wrapper
    return decorator


def track_validation_error(error_type: str):
    """
    Track validation error.

    Args:
        error_type: Type of validation error
    """
    config_validation_errors.labels(error_type=error_type).inc()


def track_auth_attempt(method: str, success: bool):
    """
    Track authentication attempt.

    Args:
        method: Authentication method (password, api_key, jwt)
        success: Whether attempt was successful
    """
    status = 'success' if success else 'failure'
    auth_attempts_total.labels(method=method, status=status).inc()


def track_api_key_use(key_id: int):
    """
    Track API key usage.

    Args:
        key_id: API key ID
    """
    api_key_usage.labels(key_id=str(key_id)).inc()


def track_db_query(operation: str):
    """
    Decorator to track database query.

    Args:
        operation: Operation type (select, insert, update, delete)

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            db_queries_total.labels(operation=operation).inc()
            with db_query_duration.labels(operation=operation).time():
                return func(*args, **kwargs)
        return wrapper
    return decorator


def track_cache_hit(cache_type: str = 'redis'):
    """
    Track cache hit.

    Args:
        cache_type: Type of cache
    """
    cache_hits_total.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str = 'redis'):
    """
    Track cache miss.

    Args:
        cache_type: Type of cache
    """
    cache_misses_total.labels(cache_type=cache_type).inc()


def track_error(error_type: str, endpoint: str = 'unknown'):
    """
    Track error occurrence.

    Args:
        error_type: Type of error
        endpoint: Endpoint where error occurred
    """
    errors_total.labels(error_type=error_type, endpoint=endpoint).inc()


def update_resource_metrics():
    """Update resource usage metrics."""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_bytes.set(memory_info.rss)
    except ImportError:
        pass  # psutil not available


def update_history_metrics():
    """Update history-related metrics."""
    try:
        from models import ConfigHistory, db
        total_entries = ConfigHistory.query.count()
        history_entries_total.set(total_entries)

        # Estimate size (rough calculation)
        # In production, you might want to store this in database
        avg_size = 5000  # Average config size in bytes
        history_size_bytes.set(total_entries * avg_size)
    except Exception:
        pass  # Database not available or error


@metrics_bp.route('/metrics')
def prometheus_metrics():
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format
    """
    # Update dynamic metrics before serving
    update_resource_metrics()
    update_history_metrics()

    # Generate metrics
    metrics_output = generate_latest(registry)

    # Return with correct content type
    from flask import Response
    return Response(metrics_output, mimetype=CONTENT_TYPE_LATEST)


@metrics_bp.route('/metrics/health')
def metrics_health():
    """
    Health check for metrics endpoint.

    Returns:
        JSON response with metrics status
    """
    from flask import jsonify
    return jsonify({
        'status': 'healthy',
        'metrics_enabled': True,
        'registry': 'prometheus'
    })
