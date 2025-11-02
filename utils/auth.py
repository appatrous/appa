"""
Authentication and authorization utilities.
Provides JWT token management and role-based access control.
"""
import jwt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any, Tuple


class AuthError(Exception):
    """Custom exception for authentication errors."""

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class JWTManager:
    """JWT token management."""

    @staticmethod
    def generate_token(user_id: int, username: str, is_admin: bool = False,
                       token_type: str = 'access') -> str:
        """
        Generate JWT token.

        Args:
            user_id: User ID
            username: Username
            is_admin: Admin flag
            token_type: 'access' or 'refresh'

        Returns:
            str: JWT token
        """
        if token_type == 'access':
            expires_delta = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        else:
            expires_delta = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']

        payload = {
            'user_id': user_id,
            'username': username,
            'is_admin': is_admin,
            'token_type': token_type,
            'exp': datetime.utcnow() + expires_delta,
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)  # JWT ID for revocation
        }

        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )

        return token

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            dict: Decoded token payload

        Raises:
            AuthError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError('Token has expired', 401)
        except jwt.InvalidTokenError as e:
            raise AuthError(f'Invalid token: {str(e)}', 401)

    @staticmethod
    def generate_token_pair(user_id: int, username: str,
                            is_admin: bool = False) -> Tuple[str, str]:
        """
        Generate access and refresh token pair.

        Args:
            user_id: User ID
            username: Username
            is_admin: Admin flag

        Returns:
            tuple: (access_token, refresh_token)
        """
        access_token = JWTManager.generate_token(
            user_id, username, is_admin, 'access'
        )
        refresh_token = JWTManager.generate_token(
            user_id, username, is_admin, 'refresh'
        )
        return access_token, refresh_token


class APIKeyManager:
    """API key management."""

    @staticmethod
    def generate_key() -> str:
        """
        Generate a secure API key.

        Returns:
            str: API key
        """
        return f"cck_{secrets.token_urlsafe(32)}"

    @staticmethod
    def validate_key_format(key: str) -> bool:
        """
        Validate API key format.

        Args:
            key: API key string

        Returns:
            bool: True if format is valid
        """
        return key.startswith('cck_') and len(key) >= 40


def get_token_from_request() -> Optional[str]:
    """
    Extract JWT token from request headers.

    Returns:
        str: Token or None
    """
    auth_header = request.headers.get('Authorization', '')

    if auth_header.startswith('Bearer '):
        return auth_header[7:]

    return None


def get_api_key_from_request() -> Optional[str]:
    """
    Extract API key from request headers.

    Returns:
        str: API key or None
    """
    return request.headers.get('X-API-Key')


def token_required(f):
    """
    Decorator to require valid JWT token.

    Usage:
        @token_required
        def protected_route():
            # Access current_user from g
            pass
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g

        token = get_token_from_request()

        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401

        try:
            payload = JWTManager.decode_token(token)

            # Verify it's an access token
            if payload.get('token_type') != 'access':
                return jsonify({'error': 'Invalid token type'}), 401

            # Store user info in Flask g object
            g.current_user = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'is_admin': payload.get('is_admin', False)
            }

        except AuthError as e:
            return jsonify({'error': e.message}), e.status_code

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    Decorator to require admin privileges.

    Usage:
        @admin_required
        def admin_route():
            pass
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g

        token = get_token_from_request()

        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401

        try:
            payload = JWTManager.decode_token(token)

            if payload.get('token_type') != 'access':
                return jsonify({'error': 'Invalid token type'}), 401

            if not payload.get('is_admin', False):
                return jsonify({'error': 'Admin privileges required'}), 403

            g.current_user = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'is_admin': True
            }

        except AuthError as e:
            return jsonify({'error': e.message}), e.status_code

        return f(*args, **kwargs)

    return decorated


def api_key_required(f):
    """
    Decorator to require valid API key.

    Usage:
        @api_key_required
        def api_route():
            # Access current_user from g
            pass
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g
        from models import APIKey

        api_key = get_api_key_from_request()

        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401

        # Validate format
        if not APIKeyManager.validate_key_format(api_key):
            return jsonify({'error': 'Invalid API key format'}), 401

        # Look up API key in database
        key_obj = APIKey.query.filter_by(is_active=True).all()

        valid_key = None
        for k in key_obj:
            if k.check_key(api_key) and not k.is_expired():
                valid_key = k
                break

        if not valid_key:
            return jsonify({'error': 'Invalid or expired API key'}), 401

        # Update last used timestamp
        valid_key.update_last_used()

        # Store user info in Flask g object
        g.current_user = {
            'user_id': valid_key.user_id,
            'username': valid_key.user.username,
            'is_admin': valid_key.user.is_admin,
            'via_api_key': True
        }

        return f(*args, **kwargs)

    return decorated


def auth_required(f):
    """
    Decorator to require either JWT token or API key.

    Usage:
        @auth_required
        def protected_route():
            pass
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g

        # Try JWT token first
        token = get_token_from_request()
        if token:
            try:
                payload = JWTManager.decode_token(token)

                if payload.get('token_type') != 'access':
                    return jsonify({'error': 'Invalid token type'}), 401

                g.current_user = {
                    'user_id': payload['user_id'],
                    'username': payload['username'],
                    'is_admin': payload.get('is_admin', False),
                    'via_api_key': False
                }

                return f(*args, **kwargs)

            except AuthError:
                pass  # Try API key next

        # Try API key
        api_key = get_api_key_from_request()
        if api_key:
            from models import APIKey

            if not APIKeyManager.validate_key_format(api_key):
                return jsonify({'error': 'Invalid API key format'}), 401

            key_obj = APIKey.query.filter_by(is_active=True).all()

            for k in key_obj:
                if k.check_key(api_key) and not k.is_expired():
                    k.update_last_used()

                    g.current_user = {
                        'user_id': k.user_id,
                        'username': k.user.username,
                        'is_admin': k.user.is_admin,
                        'via_api_key': True
                    }

                    return f(*args, **kwargs)

        return jsonify({'error': 'Authentication required'}), 401

    return decorated


def optional_auth(f):
    """
    Decorator that allows but doesn't require authentication.
    If authenticated, user info is available in g.current_user

    Usage:
        @optional_auth
        def public_route():
            from flask import g
            if hasattr(g, 'current_user'):
                # User is authenticated
                pass
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g

        # Try JWT token
        token = get_token_from_request()
        if token:
            try:
                payload = JWTManager.decode_token(token)

                if payload.get('token_type') == 'access':
                    g.current_user = {
                        'user_id': payload['user_id'],
                        'username': payload['username'],
                        'is_admin': payload.get('is_admin', False),
                        'via_api_key': False
                    }
                    return f(*args, **kwargs)

            except AuthError:
                pass

        # Try API key
        api_key = get_api_key_from_request()
        if api_key:
            from models import APIKey

            if APIKeyManager.validate_key_format(api_key):
                key_obj = APIKey.query.filter_by(is_active=True).all()

                for k in key_obj:
                    if k.check_key(api_key) and not k.is_expired():
                        k.update_last_used()

                        g.current_user = {
                            'user_id': k.user_id,
                            'username': k.user.username,
                            'is_admin': k.user.is_admin,
                            'via_api_key': True
                        }
                        break

        return f(*args, **kwargs)

    return decorated
