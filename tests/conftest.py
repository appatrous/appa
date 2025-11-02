"""
Pytest configuration and fixtures
"""
import pytest
from app import create_app
from models import db, User, ConfigHistory


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            is_admin=False
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()

        return {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }


@pytest.fixture
def admin_user(app):
    """Create an admin user."""
    with app.app_context():
        user = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        user.set_password('adminpass123')
        db.session.add(user)
        db.session.commit()

        return {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }


@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token for test user."""
    response = client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    data = response.get_json()
    return data['access_token']


@pytest.fixture
def admin_token(client, admin_user):
    """Get authentication token for admin user."""
    response = client.post('/auth/login', json={
        'username': 'admin',
        'password': 'adminpass123'
    })
    data = response.get_json()
    return data['access_token']


@pytest.fixture
def sample_config():
    """Sample configuration data."""
    return {
        'platform': 'ios',
        'hostname': 'test-router',
        'domain_name': 'example.com',
        'enable_secret': 'test123',
        'interfaces': [
            {
                'name': 'GigabitEthernet0/0',
                'description': 'WAN Interface',
                'ip_address': '192.168.1.1',
                'subnet_mask': '255.255.255.0',
                'enabled': True
            }
        ],
        'vlans': [
            {'id': 10, 'name': 'DATA'},
            {'id': 20, 'name': 'VOICE'}
        ],
        'static_routes': [
            {
                'network': '0.0.0.0/0',
                'next_hop': '192.168.1.254'
            }
        ],
        'ntp_servers': ['pool.ntp.org'],
        'output_format': 'cli'
    }
