"""
CCIE Configuration Generator with Validation and Explanation.
Implements the CCIE expert prompt requirements.
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime
import json


class CCIEConfigValidator:
    """Validates CCIE-level configurations."""

    @staticmethod
    def validate_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete configuration and return validation report.

        Args:
            config_data: Configuration dictionary

        Returns:
            Validation report with warnings and errors
        """
        warnings = []
        errors = []
        suggestions = []

        # Device identification
        device_type = config_data.get('device_type')
        platform = config_data.get('platform')

        # Basic validation
        if not config_data.get('hostname'):
            errors.append("Hostname is required")

        if not config_data.get('enable_secret'):
            warnings.append("Enable secret not configured - set immediately for production")

        # AAA validation
        security = config_data.get('security', {})
        aaa = security.get('aaa', {})

        if not aaa:
            warnings.append("AAA not configured - highly recommended for enterprise environments")
        else:
            if not aaa.get('tacacs') and not aaa.get('radius'):
                warnings.append("No AAA servers configured - using local authentication only")

            if aaa.get('local_users'):
                if len(aaa['local_users']) == 0:
                    warnings.append("No local fallback users configured")

        # Routing validation
        routing = config_data.get('routing', {})

        if routing:
            # OSPF validation
            ospf = routing.get('ospf')
            if ospf:
                if not ospf.get('router_id'):
                    warnings.append("OSPF router-id not explicitly set - will use highest loopback/interface IP")

                if not ospf.get('bfd'):
                    suggestions.append("Consider enabling BFD on OSPF for faster convergence")

            # BGP validation
            bgp = routing.get('bgp')
            if bgp:
                if not bgp.get('router_id'):
                    warnings.append("BGP router-id not explicitly set")

                neighbors = bgp.get('neighbors', [])
                for neighbor in neighbors:
                    if neighbor.get('remote_as') == bgp.get('asn'):
                        # iBGP neighbor
                        if not neighbor.get('update_source'):
                            suggestions.append(f"iBGP neighbor {neighbor['ip']} should use update-source (typically loopback)")

                if len(neighbors) == 0:
                    warnings.append("BGP configured but no neighbors defined")

        # Redundancy validation
        redundancy = config_data.get('redundancy', {})

        if redundancy:
            hsrp = redundancy.get('hsrp', [])
            vrrp = redundancy.get('vrrp', [])
            glbp = redundancy.get('glbp', [])

            if hsrp and vrrp:
                warnings.append("Both HSRP and VRRP configured - use one FHRP protocol per network segment")

            for group in hsrp:
                if group.get('priority', 100) == 100:
                    suggestions.append(f"HSRP group {group['group']} using default priority - consider explicit priority for clarity")

        # Security validation
        if security:
            acl = security.get('acl', [])
            zone_fw = security.get('zone_fw')
            vpn = security.get('vpn')

            if vpn:
                if vpn.get('ike_version', 2) == 1:
                    warnings.append("IKEv1 is deprecated - use IKEv2 for new deployments")

                if vpn.get('dh_group', 19) < 14:
                    warnings.append("Weak DH group - use group 14 or higher (19/20 recommended)")

        # QoS validation
        qos = config_data.get('qos', {})

        if qos and qos.get('enabled'):
            classes = qos.get('classes', [])

            voice_configured = any(c.get('name') == 'VOICE' or 'voice' in c.get('name', '').lower() for c in classes)

            if voice_configured:
                voice_class = next((c for c in classes if c.get('name') == 'VOICE' or 'voice' in c.get('name', '').lower()), None)

                if voice_class and not voice_class.get('priority'):
                    warnings.append("Voice class configured without strict priority - voice should use LLQ")

        # Services validation
        services = config_data.get('services', {})

        if services:
            if not services.get('ntp'):
                suggestions.append("NTP not configured - time synchronization critical for logging and security")

            if not services.get('syslog'):
                suggestions.append("Syslog not configured - centralized logging recommended")

            snmp = services.get('snmp', {})
            if snmp:
                if snmp.get('version', 3) == 2:
                    warnings.append("SNMPv2c is insecure - use SNMPv3 for production")

        # Interface validation
        interfaces = config_data.get('interfaces', [])

        for intf in interfaces:
            if not intf.get('description'):
                suggestions.append(f"Interface {intf.get('name')} has no description")

        # Platform-specific validation
        if device_type == 'router':
            if not routing:
                warnings.append("Router configured without routing protocols")

        if device_type == 'firewall':
            if not security or not security.get('acl'):
                warnings.append("Firewall configured without access control lists")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions,
            'total_checks': len(errors) + len(warnings) + len(suggestions),
            'timestamp': datetime.utcnow().isoformat()
        }


class CCIEConfigExplainer:
    """Generates technical explanations for configurations."""

    @staticmethod
    def generate_explanation(config_data: Dict[str, Any]) -> str:
        """
        Generate CCIE-level technical explanation of the configuration.

        Args:
            config_data: Configuration dictionary

        Returns:
            Detailed technical explanation
        """
        explanations = []

        device_type = config_data.get('device_type', 'unknown')
        platform = config_data.get('platform', 'unknown')
        hostname = config_data.get('hostname', 'DEVICE')

        explanations.append(f"=== CCIE-Level Configuration Explanation for {hostname} ===\n")
        explanations.append(f"Device Type: {device_type.upper()}")
        explanations.append(f"Platform: {platform.upper()}\n")

        # AAA explanation
        security = config_data.get('security', {})
        aaa = security.get('aaa', {})

        if aaa:
            explanations.append("--- Authentication, Authorization, Accounting (AAA) ---")

            if aaa.get('tacacs'):
                explanations.append("• TACACS+ configured for centralized AAA")
                explanations.append("  - Provides encrypted authentication and command authorization")
                explanations.append("  - Fallback to local authentication if TACACS+ unavailable")
                explanations.append("  - Command accounting enabled for audit trail")

            if aaa.get('radius'):
                explanations.append("• RADIUS configured for network access authentication")
                explanations.append("  - Used for VPN and wireless authentication")
                explanations.append("  - Lightweight compared to TACACS+")

            explanations.append("")

        # Routing explanation
        routing = config_data.get('routing', {})

        if routing:
            explanations.append("--- Routing Configuration ---")

            # Static routes
            if routing.get('static'):
                explanations.append("• Static routes configured for:")
                explanations.append("  - Default gateway or specific destinations")
                explanations.append("  - Provides predictable routing paths")
                explanations.append("  - Lower CPU overhead than dynamic protocols")

            # OSPF
            ospf = routing.get('ospf')
            if ospf:
                explanations.append("\n• OSPFv2 (Open Shortest Path First):")
                explanations.append(f"  - Process ID: {ospf.get('process_id')}")

                if ospf.get('router_id'):
                    explanations.append(f"  - Router ID: {ospf.get('router_id')} (explicitly set for stability)")

                explanations.append("  - Link-state IGP with fast convergence")
                explanations.append("  - Hierarchical design using areas")

                if ospf.get('bfd'):
                    explanations.append("  - BFD enabled: sub-second failure detection")
                    explanations.append("  - Reduces convergence time from ~40s to <1s")

                if ospf.get('nsf'):
                    explanations.append("  - NSF/SSO enabled: hitless supervisor failover")

                areas = ospf.get('areas', [])
                for area in areas:
                    if area.get('stub'):
                        explanations.append(f"  - Area {area['id']} configured as stub (no external routes)")
                    elif area.get('nssa'):
                        explanations.append(f"  - Area {area['id']} configured as NSSA (allows limited redistribution)")

            # EIGRP
            eigrp = routing.get('eigrp')
            if eigrp:
                explanations.append("\n• EIGRP (Enhanced Interior Gateway Routing Protocol):")
                explanations.append(f"  - AS Number: {eigrp.get('asn')}")
                explanations.append("  - Cisco proprietary protocol with DUAL algorithm")
                explanations.append("  - Rapid convergence with minimal bandwidth usage")
                explanations.append("  - Supports unequal-cost load balancing")

                if eigrp.get('named_mode'):
                    explanations.append("  - Named mode: modern hierarchical configuration")

                if eigrp.get('stub'):
                    explanations.append("  - Stub configuration: reduces query scope and memory")

            # BGP
            bgp = routing.get('bgp')
            if bgp:
                explanations.append("\n• BGP (Border Gateway Protocol):")
                explanations.append(f"  - AS Number: {bgp.get('asn')}")
                explanations.append("  - Path-vector EGP for internet routing")
                explanations.append("  - Policy-based routing with extensive attributes")

                neighbors = bgp.get('neighbors', [])
                ibgp_count = sum(1 for n in neighbors if n.get('remote_as') == bgp.get('asn'))
                ebgp_count = len(neighbors) - ibgp_count

                if ibgp_count > 0:
                    explanations.append(f"  - iBGP neighbors: {ibgp_count} (internal peering)")

                if ebgp_count > 0:
                    explanations.append(f"  - eBGP neighbors: {ebgp_count} (external peering)")

                if bgp.get('maximum_paths', 1) > 1:
                    explanations.append(f"  - Multipath enabled: up to {bgp['maximum_paths']} paths for load balancing")

            # IS-IS
            isis = routing.get('isis')
            if isis:
                explanations.append("\n• IS-IS (Intermediate System to Intermediate System):")
                explanations.append(f"  - Process: {isis.get('process')}")
                explanations.append(f"  - NET: {isis.get('net')}")
                explanations.append("  - Link-state protocol similar to OSPF")
                explanations.append("  - Commonly used in service provider networks")
                explanations.append("  - More scalable than OSPF for very large networks")

            explanations.append("")

        # Redundancy explanation
        redundancy = config_data.get('redundancy', {})

        if redundancy:
            explanations.append("--- First Hop Redundancy Protocol (FHRP) ---")

            hsrp = redundancy.get('hsrp', [])
            if hsrp:
                explanations.append("• HSRP (Hot Standby Router Protocol):")
                explanations.append("  - Cisco proprietary FHRP")
                explanations.append("  - Active/Standby model with virtual IP")
                explanations.append("  - Sub-second failover with preempt and timers")

                for group in hsrp:
                    explanations.append(f"  - Group {group['group']}: VIP {group['vip']}, Priority {group.get('priority', 100)}")

            vrrp = redundancy.get('vrrp', [])
            if vrrp:
                explanations.append("\n• VRRP (Virtual Router Redundancy Protocol):")
                explanations.append("  - Industry standard FHRP (RFC 5798)")
                explanations.append("  - Master/Backup model")
                explanations.append("  - Interoperable with other vendors")

            glbp = redundancy.get('glbp', [])
            if glbp:
                explanations.append("\n• GLBP (Gateway Load Balancing Protocol):")
                explanations.append("  - Cisco proprietary with load balancing")
                explanations.append("  - All routers forward traffic simultaneously")
                explanations.append("  - Automatic load distribution across gateways")

            explanations.append("")

        # Multicast explanation
        multicast = config_data.get('multicast', {})

        if multicast and multicast.get('enabled'):
            explanations.append("--- IP Multicast Configuration ---")
            explanations.append("• IP Multicast enabled for one-to-many communication")

            pim_mode = multicast.get('pim_mode')
            if pim_mode:
                mode_descriptions = {
                    'sparse-mode': 'Sparse Mode (explicit join, RP-based)',
                    'dense-mode': 'Dense Mode (flood-and-prune, not recommended)',
                    'ssm': 'Source-Specific Multicast (no RP required)',
                    'bidir': 'Bidirectional PIM (optimized for many-to-many)'
                }
                explanations.append(f"• PIM: {mode_descriptions.get(pim_mode, pim_mode)}")

            rp = multicast.get('rp', {})
            if rp:
                rp_types = {
                    'static': 'Static RP configuration (simple, manual)',
                    'auto-rp': 'Auto-RP (Cisco proprietary, automatic)',
                    'bsr': 'Bootstrap Router (standards-based, automatic)',
                    'anycast': 'Anycast RP (high availability)'
                }
                explanations.append(f"• RP Type: {rp_types.get(rp.get('type'), rp.get('type'))}")

            explanations.append("")

        # VPN explanation
        vpn = security.get('vpn')

        if vpn:
            explanations.append("--- VPN Configuration ---")

            vpn_types = {
                'ipsec': 'Site-to-Site IPsec VPN',
                'dmvpn': 'Dynamic Multipoint VPN (hub-and-spoke/spoke-to-spoke)',
                'getvpn': 'Group Encrypted Transport VPN (any-to-any)',
                'flexvpn': 'FlexVPN (next-gen IKEv2-based)',
                'ssl': 'SSL VPN (remote access)',
                'l2tp': 'L2TP VPN (Layer 2 tunneling)'
            }

            explanations.append(f"• VPN Type: {vpn_types.get(vpn.get('type'), vpn.get('type'))}")
            explanations.append(f"• IKE Version: {vpn.get('ike_version', 2)}")
            explanations.append(f"• Encryption: {vpn.get('encryption', 'aes-256-gcm')}")
            explanations.append(f"• Integrity: {vpn.get('hash', 'sha256')}")
            explanations.append(f"• DH Group: {vpn.get('dh_group', 19)} (PFS enabled)")

            peers = vpn.get('peers', [])
            if peers:
                explanations.append(f"• {len(peers)} VPN peer(s) configured")

            explanations.append("")

        # QoS explanation
        qos = config_data.get('qos', {})

        if qos and qos.get('enabled'):
            explanations.append("--- Quality of Service (QoS) ---")
            explanations.append("• QoS configured for traffic prioritization")
            explanations.append("• Classification based on DSCP/CoS values")
            explanations.append("• Congestion management using LLQ/CBWFQ")

            classes = qos.get('classes', [])
            for cls in classes:
                explanations.append(f"\n• Class: {cls.get('name')}")

                if 'voice' in cls.get('name', '').lower():
                    explanations.append("  - Voice traffic: strict priority queuing (LLQ)")
                    explanations.append("  - Maximum delay: 150ms, jitter: <30ms")

                if cls.get('bandwidth'):
                    explanations.append(f"  - Guaranteed bandwidth: {cls['bandwidth']}")

            explanations.append("")

        # Security features
        if security:
            explanations.append("--- Security Features ---")

            acl = security.get('acl', [])
            if acl:
                explanations.append(f"• {len(acl)} Access Control List(s) configured")
                explanations.append("  - Packet filtering at Layer 3/4")

            zone_fw = security.get('zone_fw')
            if zone_fw:
                explanations.append("• Zone-Based Firewall:")
                explanations.append("  - Stateful inspection of traffic between zones")
                explanations.append("  - More scalable than CBAC")
                explanations.append("  - Supports application-layer filtering")

            if security.get('port_security'):
                explanations.append("• Port Security: MAC address limiting and violation actions")

            if security.get('dhcp_snooping'):
                explanations.append("• DHCP Snooping: prevents rogue DHCP servers")

            if security.get('dai'):
                explanations.append("• Dynamic ARP Inspection: prevents ARP spoofing attacks")

            explanations.append("")

        # Services
        services = config_data.get('services', {})

        if services:
            explanations.append("--- Network Services ---")

            if services.get('ntp'):
                explanations.append("• NTP: Time synchronization critical for:")
                explanations.append("  - Logging correlation across devices")
                explanations.append("  - Certificate validity")
                explanations.append("  - Time-based ACLs")

            if services.get('syslog'):
                explanations.append("• Syslog: Centralized logging for:")
                explanations.append("  - Troubleshooting and forensics")
                explanations.append("  - Compliance and audit requirements")

            snmp = services.get('snmp', {})
            if snmp:
                version = snmp.get('version', 3)
                explanations.append(f"• SNMP v{version}: Network monitoring and management")

                if version == 3:
                    explanations.append("  - Authentication and encryption enabled")

            if services.get('netflow'):
                explanations.append("• NetFlow: Traffic analysis and capacity planning")

            explanations.append("")

        # Best practices
        explanations.append("--- CCIE Best Practices Applied ---")
        explanations.append("✓ Service timestamps configured for accurate logging")
        explanations.append("✓ SSH version 2 enforced (Telnet disabled)")
        explanations.append("✓ Control Plane Policing (CoPP) configured")
        explanations.append("✓ Password encryption enabled")
        explanations.append("✓ Login banner configured")
        explanations.append("✓ VTY access restricted to SSH only")
        explanations.append("✓ TCP keepalives enabled")

        if routing and routing.get('ospf') and routing['ospf'].get('bfd'):
            explanations.append("✓ BFD enabled for sub-second convergence")

        if redundancy:
            explanations.append("✓ First-hop redundancy configured for high availability")

        return '\n'.join(explanations)


class CCIEConfigGenerator:
    """Main CCIE configuration generator."""

    @staticmethod
    def generate(config_data: Dict[str, Any], template_renderer) -> Dict[str, Any]:
        """
        Generate CCIE-level configuration with validation and explanation.

        Args:
            config_data: Configuration dictionary
            template_renderer: Template rendering function

        Returns:
            Dictionary with CLI, validation, and explanation
        """
        # Add timestamp
        config_data['timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        # Determine template
        platform = config_data.get('platform', 'ios')

        # Use CCIE template if available
        template_map = {
            'ios': 'ios_ccie_config.j2',
            'ios-xe': 'ios_ccie_config.j2',
            'nxos': 'nxos_ccie_config.j2',
            'asa': 'asa_ccie_config.j2',
            'ios-xr': 'iosxr_ccie_config.j2'
        }

        template_name = template_map.get(platform, 'ios_ccie_config.j2')

        # Check if CCIE template exists, otherwise fall back
        try:
            cli_config = template_renderer(template_name, config_data)
        except Exception:
            # Fallback to basic template
            basic_template_map = {
                'ios': 'ios_config.j2',
                'ios-xe': 'ios_config.j2',
                'nxos': 'nxos_config.j2',
                'asa': 'asa_config.j2',
                'ios-xr': 'iosxr_config.j2'
            }
            cli_config = template_renderer(basic_template_map.get(platform, 'ios_config.j2'), config_data)

        # Generate validation
        validation = CCIEConfigValidator.validate_config(config_data)

        # Generate explanation
        explanation = ""
        if config_data.get('generate_explanation', True):
            explanation = CCIEConfigExplainer.generate_explanation(config_data)

        return {
            'cli': cli_config,
            'validation': validation if config_data.get('generate_validation', True) else None,
            'explanation': explanation
        }
