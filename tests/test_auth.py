"""
Tests for authentication endpoints
"""
import pytest


class TestAuthentication:
    """Tests for authentication flow."""

    def test_register_user(self, client):
        """Test user registration."""
        response = client.post('/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['user']['username'] == 'newuser'

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        response = client.post('/auth/register', json={
            'username': 'testuser',  # Already exists
            'email': 'another@example.com',
            'password': 'securepass123'
        })

        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'access_token' in data
        assert 'refresh_token' in data

    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_refresh_token(self, client, test_user):
        """Test token refresh."""
        # Login first
        login_response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })
        refresh_token = login_response.get_json()['refresh_token']

        # Refresh
        response = client.post('/auth/refresh',
                               headers={'Authorization': f'Bearer {refresh_token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data

    def test_get_current_user(self, client, auth_token):
        """Test getting current user info."""
        response = client.get('/auth/me',
                              headers={'Authorization': f'Bearer {auth_token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['username'] == 'testuser'

    def test_change_password(self, client, auth_token):
        """Test password change."""
        response = client.post('/auth/change-password',
                               json={
                                   'old_password': 'testpass123',
                                   'new_password': 'newpass456'
                               },
                               headers={'Authorization': f'Bearer {auth_token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestAPIKeys:
    """Tests for API key management."""

    def test_create_api_key(self, client, auth_token):
        """Test creating API key."""
        response = client.post('/auth/api-keys',
                               json={
                                   'name': 'Test Key',
                                   'description': 'Test description'
                               },
                               headers={'Authorization': f'Bearer {auth_token}'})

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'api_key' in data
        assert data['api_key'].startswith('cck_')

    def test_list_api_keys(self, client, auth_token):
        """Test listing API keys."""
        # Create a key first
        client.post('/auth/api-keys',
                    json={'name': 'Test Key'},
                    headers={'Authorization': f'Bearer {auth_token}'})

        # List keys
        response = client.get('/auth/api-keys',
                              headers={'Authorization': f'Bearer {auth_token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert 'api_keys' in data
        assert len(data['api_keys']) > 0

    def test_delete_api_key(self, client, auth_token):
        """Test deleting API key."""
        # Create a key
        create_response = client.post('/auth/api-keys',
                                      json={'name': 'Test Key'},
                                      headers={'Authorization': f'Bearer {auth_token}'})
        key_id = create_response.get_json()['key_info']['id']

        # Delete it
        response = client.delete(f'/auth/api-keys/{key_id}',
                                 headers={'Authorization': f'Bearer {auth_token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestAdminEndpoints:
    """Tests for admin-only endpoints."""

    def test_list_users_as_admin(self, client, admin_token):
        """Test listing users as admin."""
        response = client.get('/auth/users',
                              headers={'Authorization': f'Bearer {admin_token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data

    def test_list_users_as_regular_user(self, client, auth_token):
        """Test listing users as regular user (should fail)."""
        response = client.get('/auth/users',
                              headers={'Authorization': f'Bearer {auth_token}'})

        assert response.status_code == 403
