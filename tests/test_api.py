"""
Tests for REST API endpoints
"""
import pytest
import json


class TestAPIGenerate:
    """Tests for /api/v1/generate endpoint."""

    def test_generate_config_success(self, client, sample_config):
        """Test successful configuration generation."""
        response = client.post('/api/v1/generate',
                               json=sample_config,
                               content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()

        assert data['success'] is True
        assert data['platform'] == 'ios'
        assert data['hostname'] == 'test-router'
        assert 'configuration' in data
        assert 'hostname test-router' in data['configuration']

    def test_generate_config_invalid_platform(self, client, sample_config):
        """Test generation with invalid platform."""
        sample_config['platform'] = 'invalid'

        response = client.post('/api/v1/generate',
                               json=sample_config,
                               content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_generate_config_missing_required_field(self, client):
        """Test generation with missing required field."""
        incomplete_config = {
            'platform': 'ios'
            # Missing hostname
        }

        response = client.post('/api/v1/generate',
                               json=incomplete_config,
                               content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_generate_config_all_platforms(self, client):
        """Test generation for all supported platforms."""
        platforms = ['ios', 'nxos', 'asa', 'iosxr']

        for platform in platforms:
            config = {
                'platform': platform,
                'hostname': f'test-{platform}',
                'output_format': 'cli'
            }

            response = client.post('/api/v1/generate',
                                   json=config,
                                   content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            assert data['platform'] == platform

    def test_generate_config_json_format(self, client):
        """Test JSON output format."""
        config = {
            'platform': 'ios',
            'hostname': 'test-router',
            'output_format': 'json'
        }

        response = client.post('/api/v1/generate',
                               json=config,
                               content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert data['output_format'] == 'json'

        # Verify configuration is valid JSON
        config_data = json.loads(data['configuration'])
        assert config_data['platform'] == 'ios'
        assert config_data['hostname'] == 'test-router'

    def test_generate_config_yaml_format(self, client):
        """Test YAML output format."""
        config = {
            'platform': 'ios',
            'hostname': 'test-router',
            'output_format': 'yaml'
        }

        response = client.post('/api/v1/generate',
                               json=config,
                               content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert data['output_format'] == 'yaml'
        assert 'platform:' in data['configuration']


class TestAPIValidate:
    """Tests for /api/v1/validate endpoint."""

    def test_validate_valid_config(self, client, sample_config):
        """Test validation of valid configuration."""
        response = client.post('/api/v1/validate',
                               json=sample_config,
                               content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is True

    def test_validate_invalid_config(self, client):
        """Test validation of invalid configuration."""
        invalid_config = {
            'platform': 'invalid_platform',
            'hostname': 'test'
        }

        response = client.post('/api/v1/validate',
                               json=invalid_config,
                               content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is False
        assert 'error' in data


class TestAPIPlatforms:
    """Tests for /api/v1/platforms endpoint."""

    def test_list_platforms(self, client):
        """Test listing supported platforms."""
        response = client.get('/api/v1/platforms')

        assert response.status_code == 200
        data = response.get_json()
        assert 'platforms' in data
        assert 'ios' in data['platforms']
        assert 'nxos' in data['platforms']
        assert 'asa' in data['platforms']


class TestAPISchema:
    """Tests for /api/v1/schema endpoint."""

    def test_get_schema(self, client):
        """Test getting API schema."""
        response = client.get('/api/v1/schema')

        assert response.status_code == 200
        data = response.get_json()
        assert 'version' in data
        assert 'schema' in data
        assert 'example' in data
