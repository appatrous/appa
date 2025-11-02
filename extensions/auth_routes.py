"""
Authentication Blueprint
Provides endpoints for user authentication, registration, and API key management.
"""
from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate, ValidationError as MarshmallowValidationError
from datetime import datetime
from models import db, User, APIKey
from utils.auth import (
    JWTManager, APIKeyManager, token_required, admin_required, auth_required
)


auth_bp = Blueprint('auth', __name__)


# Marshmallow schemas
class LoginSchema(Schema):
    """Login request schema."""
    username = fields.Str(required=True)
    password = fields.Str(required=True)


class RegisterSchema(Schema):
    """User registration schema."""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))


class PasswordChangeSchema(Schema):
    """Password change schema."""
    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8))


class APIKeyCreateSchema(Schema):
    """API key creation schema."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False)
    expires_days = fields.Int(required=False, validate=validate.Range(min=1))


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.

    Request body:
        - username: Username
        - password: Password

    Returns:
        JSON response with JWT tokens
    """
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()

    # Validate input
    schema = LoginSchema()
    try:
        validated_data = schema.load(data)
    except MarshmallowValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'details': e.messages
        }), 400

    # Find user
    user = User.query.filter_by(username=validated_data['username']).first()

    if not user or not user.check_password(validated_data['password']):
        return jsonify({
            'error': 'Invalid credentials',
            'message': 'Username or password is incorrect'
        }), 401

    if not user.is_active:
        return jsonify({
            'error': 'Account disabled',
            'message': 'Your account has been disabled'
        }), 403

    # Update last login
    user.update_last_login()

    # Generate tokens
    access_token, refresh_token = JWTManager.generate_token_pair(
        user.id, user.username, user.is_admin
    )

    return jsonify({
        'success': True,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint.

    Request body:
        - username: Username (3-80 chars)
        - email: Email address
        - password: Password (min 8 chars)

    Returns:
        JSON response with user info
    """
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()

    # Validate input
    schema = RegisterSchema()
    try:
        validated_data = schema.load(data)
    except MarshmallowValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'details': e.messages
        }), 400

    # Check if username exists
    if User.query.filter_by(username=validated_data['username']).first():
        return jsonify({
            'error': 'Username already exists',
            'message': f"Username '{validated_data['username']}' is already taken"
        }), 409

    # Check if email exists
    if User.query.filter_by(email=validated_data['email']).first():
        return jsonify({
            'error': 'Email already exists',
            'message': f"Email '{validated_data['email']}' is already registered"
        }), 409

    # Create user
    user = User(
        username=validated_data['username'],
        email=validated_data['email']
    )
    user.set_password(validated_data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token using refresh token.

    Request headers:
        - Authorization: Bearer <refresh_token>

    Returns:
        JSON response with new access token
    """
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return jsonify({
            'error': 'Missing refresh token'
        }), 401

    refresh_token = auth_header[7:]

    try:
        payload = JWTManager.decode_token(refresh_token)

        # Verify it's a refresh token
        if payload.get('token_type') != 'refresh':
            return jsonify({
                'error': 'Invalid token type',
                'message': 'This endpoint requires a refresh token'
            }), 401

        # Generate new access token
        access_token = JWTManager.generate_token(
            payload['user_id'],
            payload['username'],
            payload.get('is_admin', False),
            'access'
        )

        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Invalid refresh token',
            'message': str(e)
        }), 401


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """
    Get current authenticated user info.

    Returns:
        JSON response with user info
    """
    user = User.query.get(g.current_user['user_id'])

    if not user:
        return jsonify({
            'error': 'User not found'
        }), 404

    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """
    Change user password.

    Request body:
        - old_password: Current password
        - new_password: New password

    Returns:
        JSON response with success message
    """
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()

    # Validate input
    schema = PasswordChangeSchema()
    try:
        validated_data = schema.load(data)
    except MarshmallowValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'details': e.messages
        }), 400

    # Get user
    user = User.query.get(g.current_user['user_id'])

    if not user:
        return jsonify({
            'error': 'User not found'
        }), 404

    # Verify old password
    if not user.check_password(validated_data['old_password']):
        return jsonify({
            'error': 'Invalid password',
            'message': 'Current password is incorrect'
        }), 401

    # Set new password
    user.set_password(validated_data['new_password'])
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Password changed successfully'
    }), 200


@auth_bp.route('/api-keys', methods=['GET'])
@token_required
def list_api_keys():
    """
    List user's API keys.

    Returns:
        JSON response with API keys list
    """
    keys = APIKey.query.filter_by(
        user_id=g.current_user['user_id']
    ).order_by(APIKey.created_at.desc()).all()

    return jsonify({
        'success': True,
        'api_keys': [key.to_dict() for key in keys]
    }), 200


@auth_bp.route('/api-keys', methods=['POST'])
@token_required
def create_api_key():
    """
    Create new API key.

    Request body:
        - name: Key name
        - description: Optional description
        - expires_days: Optional expiration in days

    Returns:
        JSON response with new API key (shown only once!)
    """
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()

    # Validate input
    schema = APIKeyCreateSchema()
    try:
        validated_data = schema.load(data)
    except MarshmallowValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'details': e.messages
        }), 400

    # Generate API key
    api_key = APIKeyManager.generate_key()

    # Calculate expiration
    expires_at = None
    if 'expires_days' in validated_data:
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(days=validated_data['expires_days'])

    # Create database record
    key_obj = APIKey(
        user_id=g.current_user['user_id'],
        name=validated_data['name'],
        description=validated_data.get('description'),
        expires_at=expires_at
    )
    key_obj.set_key(api_key)

    db.session.add(key_obj)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'API key created successfully',
        'api_key': api_key,  # Only shown once!
        'key_info': key_obj.to_dict(),
        'warning': 'Save this key now. You will not be able to see it again!'
    }), 201


@auth_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@token_required
def delete_api_key(key_id):
    """
    Delete API key.

    Args:
        key_id: API key ID

    Returns:
        JSON response with deletion confirmation
    """
    key = APIKey.query.get(key_id)

    if not key:
        return jsonify({
            'error': 'Not Found',
            'message': 'API key not found'
        }), 404

    # Check authorization
    if key.user_id != g.current_user['user_id']:
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to delete this API key'
        }), 403

    db.session.delete(key)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'API key deleted successfully'
    }), 200


@auth_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """
    List all users (admin only).

    Returns:
        JSON response with users list
    """
    users = User.query.order_by(User.created_at.desc()).all()

    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in users]
    }), 200


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    Delete user (admin only).

    Args:
        user_id: User ID

    Returns:
        JSON response with deletion confirmation
    """
    user = User.query.get(user_id)

    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': 'User not found'
        }), 404

    # Prevent deleting self
    if user.id == g.current_user['user_id']:
        return jsonify({
            'error': 'Forbidden',
            'message': 'You cannot delete your own account'
        }), 403

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'User deleted successfully'
    }), 200
