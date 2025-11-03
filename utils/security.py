"""
Security utilities and middleware.
Provides security headers, CORS management, and other security features.
"""
from functools import wraps
from flask import request, make_response
import secrets
import hashlib


class SecurityHeaders:
    """
    Security headers middleware for Flask.
    Adds security-related HTTP headers to all responses.
    """

    def __init__(self, app=None):
        """
        Initialize security headers middleware.

        Args:
            app: Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize the Flask application with security headers.

        Args:
            app: Flask application instance
        """
        self.app = app

        # Register after_request handler
        app.after_request(self.add_security_headers)

        # Store CSP nonce in app config
        app.config.setdefault('CSP_NONCE_ENABLED', True)

    @staticmethod
    def generate_csp_nonce():
        """
        Generate a cryptographically secure nonce for CSP.

        Returns:
            str: Base64-encoded nonce
        """
        return secrets.token_urlsafe(16)

    def add_security_headers(self, response):
        """
        Add security headers to response.

        Args:
            response: Flask response object

        Returns:
            Response with security headers added
        """
        # Strict-Transport-Security (HSTS)
        # Force HTTPS for 1 year, include subdomains
        if self.app.config.get('SESSION_COOKIE_SECURE', False):
            response.headers['Strict-Transport-Security'] = \
                'max-age=31536000; includeSubDomains; preload'

        # X-Content-Type-Options
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # X-Frame-Options
        # Prevent clickjacking attacks
        response.headers['X-Frame-Options'] = 'DENY'

        # X-XSS-Protection
        # Enable browser XSS protection (legacy, but doesn't hurt)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer-Policy
        # Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions-Policy (formerly Feature-Policy)
        # Disable unnecessary browser features
        permissions_policy = [
            'geolocation=()',
            'microphone=()',
            'camera=()',
            'payment=()',
            'usb=()',
            'magnetometer=()',
            'gyroscope=()',
            'accelerometer=()'
        ]
        response.headers['Permissions-Policy'] = ', '.join(permissions_policy)

        # Content-Security-Policy
        # Comprehensive CSP to prevent XSS and other attacks
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # TODO: Remove unsafe-* in production
            "style-src 'self' 'unsafe-inline'",  # For Bootstrap inline styles
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests"
        ]

        # Add nonce for inline scripts if enabled
        if self.app.config.get('CSP_NONCE_ENABLED', False):
            nonce = self.generate_csp_nonce()
            # Store nonce in g for template access
            from flask import g
            g.csp_nonce = nonce
            # Update CSP with nonce
            csp_directives = [
                d.replace("'unsafe-inline'", f"'nonce-{nonce}'")
                if d.startswith('script-src') else d
                for d in csp_directives
            ]

        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

        # Cache-Control for sensitive endpoints
        if request.path.startswith('/auth') or request.path.startswith('/history'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        return response


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message="Rate limit exceeded", retry_after=None):
        """
        Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
        """
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


def require_api_key_or_jwt(f):
    """
    Decorator to require either API key or JWT authentication.

    Args:
        f: Function to decorate

    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from utils.auth import validate_api_key, decode_jwt_token

        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            try:
                user = validate_api_key(api_key)
                request.current_user = user
                return f(*args, **kwargs)
            except Exception:
                pass

        # Check for JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = decode_jwt_token(token)
                request.current_user_id = payload.get('user_id')
                return f(*args, **kwargs)
            except Exception:
                pass

        # No valid authentication
        from flask import jsonify
        return jsonify({'error': 'Authentication required'}), 401

    return decorated_function


def generate_request_id():
    """
    Generate a unique request ID for tracing.

    Returns:
        str: Unique request ID
    """
    return secrets.token_hex(16)


def hash_sensitive_data(data: str) -> str:
    """
    Hash sensitive data for logging/storage.

    Args:
        data: Data to hash

    Returns:
        SHA256 hash of data
    """
    return hashlib.sha256(data.encode()).hexdigest()


class AuditLogger:
    """Audit logging for security-sensitive operations."""

    @staticmethod
    def log_authentication(username: str, success: bool, ip_address: str, user_agent: str = None):
        """
        Log authentication attempt.

        Args:
            username: Username attempting authentication
            success: Whether authentication succeeded
            ip_address: IP address of requester
            user_agent: User agent string
        """
        from flask import current_app
        current_app.logger.info(
            f"AUTH: user={username} success={success} ip={ip_address} ua={user_agent}"
        )

    @staticmethod
    def log_api_key_usage(key_id: int, endpoint: str, ip_address: str):
        """
        Log API key usage.

        Args:
            key_id: API key ID
            endpoint: Endpoint accessed
            ip_address: IP address
        """
        from flask import current_app
        current_app.logger.info(
            f"API_KEY: key_id={key_id} endpoint={endpoint} ip={ip_address}"
        )

    @staticmethod
    def log_config_generation(user_id: int, platform: str, ip_address: str):
        """
        Log configuration generation.

        Args:
            user_id: User ID
            platform: Platform type
            ip_address: IP address
        """
        from flask import current_app
        current_app.logger.info(
            f"CONFIG_GEN: user_id={user_id} platform={platform} ip={ip_address}"
        )

    @staticmethod
    def log_admin_action(user_id: int, action: str, target: str, ip_address: str):
        """
        Log administrative action.

        Args:
            user_id: Admin user ID
            action: Action performed
            target: Target of action
            ip_address: IP address
        """
        from flask import current_app
        current_app.logger.warning(
            f"ADMIN: user_id={user_id} action={action} target={target} ip={ip_address}"
        )

    @staticmethod
    def log_security_event(event_type: str, details: dict, severity: str = 'WARNING'):
        """
        Log security event.

        Args:
            event_type: Type of security event
            details: Event details
            severity: Log severity (INFO, WARNING, ERROR, CRITICAL)
        """
        from flask import current_app
        log_func = getattr(current_app.logger, severity.lower(), current_app.logger.warning)
        log_func(f"SECURITY: type={event_type} details={details}")


def get_client_ip():
    """
    Get client IP address, considering proxies.

    Returns:
        str: Client IP address
    """
    # Check for X-Forwarded-For header (proxy/load balancer)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()

    # Check for X-Real-IP header
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')

    # Fall back to remote_addr
    return request.remote_addr or '0.0.0.0'


def sanitize_input(data: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        data: Input data to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValueError: If input is too long
    """
    if len(data) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")

    # Remove null bytes
    data = data.replace('\x00', '')

    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in data if ord(char) >= 32 or char in '\n\t')

    return sanitized.strip()
