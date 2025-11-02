"""
Input validation utilities for network configurations.
Provides strict validation for IP addresses, VLAN IDs, routing configurations, etc.
"""
import re
import ipaddress
from typing import Dict, List, Any, Optional, Union


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class NetworkValidator:
    """Validator for network-related inputs."""

    # Hostname pattern: alphanumeric, hyphens, underscores, 1-63 chars
    HOSTNAME_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-_]{0,61}[a-zA-Z0-9])?$')

    # Interface patterns
    IOS_INTERFACE_PATTERN = re.compile(
        r'^(GigabitEthernet|FastEthernet|Ethernet|Loopback|Vlan|Tunnel|Port-channel)'
        r'\d+(/\d+)*(\.\d+)?$',
        re.IGNORECASE
    )

    NXOS_INTERFACE_PATTERN = re.compile(
        r'^(Ethernet|loopback|Vlan|port-channel|mgmt)\d+(/\d+)*(\.\d+)?$',
        re.IGNORECASE
    )

    ASA_INTERFACE_PATTERN = re.compile(
        r'^(GigabitEthernet|Management|Vlan)\d+(/\d+)*(\.\d+)?$',
        re.IGNORECASE
    )

    @staticmethod
    def validate_ip_address(ip: str, allow_mask: bool = False) -> bool:
        """
        Validate IPv4 or IPv6 address.

        Args:
            ip: IP address string
            allow_mask: Allow CIDR notation (e.g., 192.168.1.0/24)

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        try:
            if allow_mask:
                ipaddress.ip_network(ip, strict=False)
            else:
                ipaddress.ip_address(ip)
            return True
        except ValueError as e:
            raise ValidationError(f"Invalid IP address '{ip}': {str(e)}")

    @staticmethod
    def validate_subnet_mask(mask: str) -> bool:
        """
        Validate subnet mask format.

        Args:
            mask: Subnet mask (e.g., 255.255.255.0 or /24)

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        # CIDR notation
        if mask.startswith('/'):
            try:
                prefix_len = int(mask[1:])
                if not 0 <= prefix_len <= 32:
                    raise ValidationError(f"Invalid CIDR prefix length: {prefix_len}")
                return True
            except ValueError:
                raise ValidationError(f"Invalid CIDR notation: {mask}")

        # Dotted decimal notation
        try:
            mask_int = int(ipaddress.IPv4Address(mask))
            # Check if it's a valid subnet mask (contiguous 1s followed by 0s)
            if mask_int == 0:
                raise ValidationError("Subnet mask cannot be 0.0.0.0")

            # Convert to binary and check for contiguous 1s
            binary = bin(mask_int)[2:].zfill(32)
            if '01' in binary:
                raise ValidationError(f"Invalid subnet mask: {mask}")

            return True
        except ipaddress.AddressValueError:
            raise ValidationError(f"Invalid subnet mask format: {mask}")

    @staticmethod
    def validate_vlan_id(vlan_id: Union[int, str]) -> bool:
        """
        Validate VLAN ID (1-4094).

        Args:
            vlan_id: VLAN ID

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        try:
            vlan = int(vlan_id)
            if not 1 <= vlan <= 4094:
                raise ValidationError(f"VLAN ID must be between 1-4094, got {vlan}")
            return True
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid VLAN ID: {vlan_id}")

    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """
        Validate hostname format.

        Args:
            hostname: Hostname string

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        if not hostname:
            raise ValidationError("Hostname cannot be empty")

        if len(hostname) > 63:
            raise ValidationError(f"Hostname too long (max 63 chars): {hostname}")

        if not NetworkValidator.HOSTNAME_PATTERN.match(hostname):
            raise ValidationError(
                f"Invalid hostname format: {hostname}. "
                "Must contain only alphanumeric, hyphens, underscores"
            )

        return True

    @staticmethod
    def validate_interface(interface: str, platform: str) -> bool:
        """
        Validate interface name based on platform.

        Args:
            interface: Interface name
            platform: Platform type (ios, nxos, asa)

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        patterns = {
            'ios': NetworkValidator.IOS_INTERFACE_PATTERN,
            'iosxr': NetworkValidator.IOS_INTERFACE_PATTERN,
            'nxos': NetworkValidator.NXOS_INTERFACE_PATTERN,
            'asa': NetworkValidator.ASA_INTERFACE_PATTERN
        }

        pattern = patterns.get(platform.lower())
        if not pattern:
            raise ValidationError(f"Unknown platform: {platform}")

        if not pattern.match(interface):
            raise ValidationError(
                f"Invalid interface format for {platform}: {interface}"
            )

        return True

    @staticmethod
    def validate_ospf_process_id(process_id: Union[int, str]) -> bool:
        """
        Validate OSPF process ID (1-65535).

        Args:
            process_id: OSPF process ID

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        try:
            pid = int(process_id)
            if not 1 <= pid <= 65535:
                raise ValidationError(
                    f"OSPF process ID must be between 1-65535, got {pid}"
                )
            return True
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid OSPF process ID: {process_id}")

    @staticmethod
    def validate_ospf_area(area: Union[int, str]) -> bool:
        """
        Validate OSPF area (0-4294967295 or dotted decimal).

        Args:
            area: OSPF area

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        # Try numeric format first
        try:
            area_int = int(area)
            if not 0 <= area_int <= 4294967295:
                raise ValidationError(f"OSPF area out of range: {area}")
            return True
        except (ValueError, TypeError):
            pass

        # Try dotted decimal format
        try:
            NetworkValidator.validate_ip_address(str(area), allow_mask=False)
            return True
        except ValidationError:
            raise ValidationError(f"Invalid OSPF area format: {area}")

    @staticmethod
    def validate_as_number(asn: Union[int, str]) -> bool:
        """
        Validate BGP AS number (1-4294967295).

        Args:
            asn: AS number

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        try:
            as_num = int(asn)
            if not 1 <= as_num <= 4294967295:
                raise ValidationError(f"AS number must be 1-4294967295, got {as_num}")
            return True
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid AS number: {asn}")

    @staticmethod
    def validate_port(port: Union[int, str]) -> bool:
        """
        Validate TCP/UDP port number (1-65535).

        Args:
            port: Port number

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        try:
            port_num = int(port)
            if not 1 <= port_num <= 65535:
                raise ValidationError(f"Port must be 1-65535, got {port_num}")
            return True
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid port number: {port}")


class ConfigValidator:
    """Validator for complete configuration structures."""

    @staticmethod
    def validate_platform(platform: str, supported_platforms: List[str]) -> bool:
        """
        Validate platform is supported.

        Args:
            platform: Platform name
            supported_platforms: List of supported platforms

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        if platform.lower() not in [p.lower() for p in supported_platforms]:
            raise ValidationError(
                f"Unsupported platform: {platform}. "
                f"Supported: {', '.join(supported_platforms)}"
            )
        return True

    @staticmethod
    def validate_static_routes(routes: List[Dict[str, Any]]) -> bool:
        """
        Validate static route configurations.

        Args:
            routes: List of route dictionaries

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        if not isinstance(routes, list):
            raise ValidationError("Routes must be a list")

        for i, route in enumerate(routes):
            if not isinstance(route, dict):
                raise ValidationError(f"Route {i} must be a dictionary")

            # Validate required fields
            if 'network' not in route:
                raise ValidationError(f"Route {i} missing 'network' field")

            if 'next_hop' not in route:
                raise ValidationError(f"Route {i} missing 'next_hop' field")

            # Validate network
            NetworkValidator.validate_ip_address(route['network'], allow_mask=True)

            # Validate next hop (can be IP or interface)
            next_hop = route['next_hop']
            if not next_hop:
                raise ValidationError(f"Route {i} next_hop cannot be empty")

            # Try to validate as IP, if fails, assume it's an interface
            try:
                NetworkValidator.validate_ip_address(next_hop)
            except ValidationError:
                # Assume it's an interface, skip validation for now
                pass

        return True

    @staticmethod
    def validate_vlans(vlans: List[Dict[str, Any]]) -> bool:
        """
        Validate VLAN configurations.

        Args:
            vlans: List of VLAN dictionaries

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        if not isinstance(vlans, list):
            raise ValidationError("VLANs must be a list")

        vlan_ids = set()

        for i, vlan in enumerate(vlans):
            if not isinstance(vlan, dict):
                raise ValidationError(f"VLAN {i} must be a dictionary")

            # Validate required fields
            if 'id' not in vlan:
                raise ValidationError(f"VLAN {i} missing 'id' field")

            vlan_id = vlan['id']
            NetworkValidator.validate_vlan_id(vlan_id)

            # Check for duplicate VLAN IDs
            if vlan_id in vlan_ids:
                raise ValidationError(f"Duplicate VLAN ID: {vlan_id}")
            vlan_ids.add(vlan_id)

            # Validate name if present
            if 'name' in vlan and not vlan['name']:
                raise ValidationError(f"VLAN {vlan_id} name cannot be empty")

        return True

    @staticmethod
    def validate_ntp_servers(servers: List[str]) -> bool:
        """
        Validate NTP server addresses.

        Args:
            servers: List of NTP server addresses

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        if not isinstance(servers, list):
            raise ValidationError("NTP servers must be a list")

        for server in servers:
            if not server:
                raise ValidationError("NTP server address cannot be empty")

            # Try IP validation, if fails, assume it's a hostname
            try:
                NetworkValidator.validate_ip_address(server)
            except ValidationError:
                # Could be a hostname, basic validation
                if len(server) > 255:
                    raise ValidationError(f"NTP server name too long: {server}")

        return True


def validate_config_data(data: Dict[str, Any], supported_platforms: List[str]) -> bool:
    """
    Main validation function for configuration data.

    Args:
        data: Configuration dictionary
        supported_platforms: List of supported platforms

    Returns:
        bool: True if all validations pass

    Raises:
        ValidationError: If any validation fails
    """
    # Validate required top-level fields
    if 'platform' not in data:
        raise ValidationError("Missing required field: platform")

    if 'hostname' not in data:
        raise ValidationError("Missing required field: hostname")

    # Validate platform
    ConfigValidator.validate_platform(data['platform'], supported_platforms)

    # Validate hostname
    NetworkValidator.validate_hostname(data['hostname'])

    # Validate optional sections
    if 'static_routes' in data and data['static_routes']:
        ConfigValidator.validate_static_routes(data['static_routes'])

    if 'vlans' in data and data['vlans']:
        ConfigValidator.validate_vlans(data['vlans'])

    if 'ntp_servers' in data and data['ntp_servers']:
        ConfigValidator.validate_ntp_servers(data['ntp_servers'])

    if 'ospf' in data and data['ospf']:
        ospf = data['ospf']
        if 'process_id' in ospf:
            NetworkValidator.validate_ospf_process_id(ospf['process_id'])
        if 'router_id' in ospf:
            NetworkValidator.validate_ip_address(ospf['router_id'])
        if 'networks' in ospf and isinstance(ospf['networks'], list):
            for net in ospf['networks']:
                if 'network' in net:
                    NetworkValidator.validate_ip_address(net['network'], allow_mask=True)
                if 'area' in net:
                    NetworkValidator.validate_ospf_area(net['area'])

    return True
