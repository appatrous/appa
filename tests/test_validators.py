"""
Tests for validation utilities
"""
import pytest
from utils.validators import (
    NetworkValidator, ConfigValidator, ValidationError,
    validate_config_data
)


class TestNetworkValidator:
    """Tests for NetworkValidator class."""

    def test_valid_ipv4(self):
        """Test valid IPv4 address validation."""
        assert NetworkValidator.validate_ip_address('192.168.1.1') is True
        assert NetworkValidator.validate_ip_address('10.0.0.1') is True

    def test_valid_ipv4_with_cidr(self):
        """Test valid IPv4 with CIDR notation."""
        assert NetworkValidator.validate_ip_address('192.168.1.0/24', allow_mask=True) is True
        assert NetworkValidator.validate_ip_address('10.0.0.0/8', allow_mask=True) is True

    def test_invalid_ip(self):
        """Test invalid IP address."""
        with pytest.raises(ValidationError):
            NetworkValidator.validate_ip_address('999.999.999.999')

        with pytest.raises(ValidationError):
            NetworkValidator.validate_ip_address('invalid')

    def test_valid_subnet_mask(self):
        """Test valid subnet mask."""
        assert NetworkValidator.validate_subnet_mask('255.255.255.0') is True
        assert NetworkValidator.validate_subnet_mask('/24') is True
        assert NetworkValidator.validate_subnet_mask('/8') is True

    def test_invalid_subnet_mask(self):
        """Test invalid subnet mask."""
        with pytest.raises(ValidationError):
            NetworkValidator.validate_subnet_mask('255.255.255.1')  # Invalid mask

        with pytest.raises(ValidationError):
            NetworkValidator.validate_subnet_mask('/33')  # Out of range

    def test_valid_vlan_id(self):
        """Test valid VLAN ID."""
        assert NetworkValidator.validate_vlan_id(1) is True
        assert NetworkValidator.validate_vlan_id(4094) is True
        assert NetworkValidator.validate_vlan_id('100') is True

    def test_invalid_vlan_id(self):
        """Test invalid VLAN ID."""
        with pytest.raises(ValidationError):
            NetworkValidator.validate_vlan_id(0)

        with pytest.raises(ValidationError):
            NetworkValidator.validate_vlan_id(4095)

        with pytest.raises(ValidationError):
            NetworkValidator.validate_vlan_id('invalid')

    def test_valid_hostname(self):
        """Test valid hostname."""
        assert NetworkValidator.validate_hostname('router01') is True
        assert NetworkValidator.validate_hostname('test-router') is True
        assert NetworkValidator.validate_hostname('R1') is True

    def test_invalid_hostname(self):
        """Test invalid hostname."""
        with pytest.raises(ValidationError):
            NetworkValidator.validate_hostname('')

        with pytest.raises(ValidationError):
            NetworkValidator.validate_hostname('a' * 64)  # Too long

    def test_valid_interface(self):
        """Test valid interface names."""
        assert NetworkValidator.validate_interface('GigabitEthernet0/0', 'ios') is True
        assert NetworkValidator.validate_interface('Ethernet1/1', 'nxos') is True
        assert NetworkValidator.validate_interface('GigabitEthernet0', 'asa') is True

    def test_invalid_interface(self):
        """Test invalid interface names."""
        with pytest.raises(ValidationError):
            NetworkValidator.validate_interface('Invalid0/0', 'ios')

    def test_valid_ospf_process_id(self):
        """Test valid OSPF process ID."""
        assert NetworkValidator.validate_ospf_process_id(1) is True
        assert NetworkValidator.validate_ospf_process_id(65535) is True

    def test_invalid_ospf_process_id(self):
        """Test invalid OSPF process ID."""
        with pytest.raises(ValidationError):
            NetworkValidator.validate_ospf_process_id(0)

        with pytest.raises(ValidationError):
            NetworkValidator.validate_ospf_process_id(65536)


class TestConfigValidator:
    """Tests for ConfigValidator class."""

    def test_valid_platform(self):
        """Test valid platform."""
        platforms = ['ios', 'nxos', 'asa', 'iosxr']
        assert ConfigValidator.validate_platform('ios', platforms) is True

    def test_invalid_platform(self):
        """Test invalid platform."""
        platforms = ['ios', 'nxos', 'asa']

        with pytest.raises(ValidationError):
            ConfigValidator.validate_platform('invalid', platforms)

    def test_valid_static_routes(self):
        """Test valid static routes."""
        routes = [
            {'network': '0.0.0.0/0', 'next_hop': '192.168.1.254'},
            {'network': '10.0.0.0/8', 'next_hop': '172.16.0.1'}
        ]

        assert ConfigValidator.validate_static_routes(routes) is True

    def test_invalid_static_routes(self):
        """Test invalid static routes."""
        invalid_routes = [
            {'network': 'invalid', 'next_hop': '192.168.1.254'}
        ]

        with pytest.raises(ValidationError):
            ConfigValidator.validate_static_routes(invalid_routes)

    def test_valid_vlans(self):
        """Test valid VLANs."""
        vlans = [
            {'id': 10, 'name': 'DATA'},
            {'id': 20, 'name': 'VOICE'}
        ]

        assert ConfigValidator.validate_vlans(vlans) is True

    def test_duplicate_vlan_ids(self):
        """Test duplicate VLAN IDs."""
        vlans = [
            {'id': 10, 'name': 'DATA'},
            {'id': 10, 'name': 'DUPLICATE'}
        ]

        with pytest.raises(ValidationError):
            ConfigValidator.validate_vlans(vlans)

    def test_valid_ntp_servers(self):
        """Test valid NTP servers."""
        servers = ['pool.ntp.org', '192.168.1.100', 'time.google.com']

        assert ConfigValidator.validate_ntp_servers(servers) is True


class TestCompleteValidation:
    """Tests for complete configuration validation."""

    def test_valid_complete_config(self):
        """Test valid complete configuration."""
        config = {
            'platform': 'ios',
            'hostname': 'router01',
            'vlans': [
                {'id': 10, 'name': 'DATA'}
            ],
            'static_routes': [
                {'network': '0.0.0.0/0', 'next_hop': '192.168.1.254'}
            ],
            'ntp_servers': ['pool.ntp.org']
        }

        platforms = ['ios', 'nxos', 'asa', 'iosxr']
        assert validate_config_data(config, platforms) is True

    def test_missing_required_field(self):
        """Test configuration with missing required field."""
        config = {
            'platform': 'ios'
            # Missing hostname
        }

        platforms = ['ios', 'nxos', 'asa']

        with pytest.raises(ValidationError):
            validate_config_data(config, platforms)
