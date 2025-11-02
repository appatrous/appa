"""
CCIE Configuration Generation API
Advanced endpoint for CCIE-level configurations with full protocol support.
"""
from flask import Blueprint, request, jsonify, current_app, g
from marshmallow import ValidationError as MarshmallowValidationError

from models import db, ConfigHistory
from utils.validators import ValidationError
from utils.auth import auth_required, optional_auth
from utils.renderer import RenderError
from utils.ccie_generator import CCIEConfigGenerator
from extensions.ccie_schemas import CCIEConfigSchema


ccie_api_bp = Blueprint('ccie_api', __name__)


@ccie_api_bp.route('/generate-ccie', methods=['POST'])
@optional_auth
def generate_ccie_config():
    """
    Generate CCIE-level configuration with full protocol support.

    This endpoint supports ALL Cisco protocols:
    - L2: VLANs, STP, EtherChannel, VTP, QinQ, PVLAN, etc.
    - L3: Static, OSPF, EIGRP, IS-IS, RIP, BGP, PBR, VRF, MPLS, etc.
    - Multicast: IGMP, PIM-SM/DM/SSM/BIDIR, MSDP, Auto-RP, etc.
    - VPN: IPsec, GRE, DMVPN, FlexVPN, GETVPN, SSL VPN, etc.
    - Security: ACL, ZBFW, IPS, TrustSec, 802.1X, etc.
    - QoS: LLQ, CBWFQ, Shaping, Policing, WRED, etc.
    - Services: NAT, DHCP, DNS, SNMP, Syslog, NTP, NetFlow, etc.

    Returns:
        JSON response with:
        - cli: Complete CLI configuration
        - validation: Validation report (errors, warnings, suggestions)
        - explanation: CCIE-level technical explanation
    """
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()

    # Validate with extended CCIE schema
    schema = CCIEConfigSchema()
    try:
        validated_data = schema.load(data)
    except MarshmallowValidationError as e:
        return jsonify({
            'error': 'Schema Validation Error',
            'details': e.messages,
            'hint': 'Check the CCIE API documentation for supported fields'
        }), 400

    # Extract platform and output format
    platform = validated_data.get('platform', 'ios')
    output_format = validated_data.pop('output_format', 'cli')

    # Custom rendering function
    def template_renderer(template_name, config_data):
        from jinja2 import Environment, FileSystemLoader
        import os

        template_dir = current_app.config['TEMPLATE_DIR']
        env = Environment(loader=FileSystemLoader(str(template_dir)))

        try:
            template = env.get_template(template_name)
            return template.render(**config_data)
        except Exception as e:
            raise RenderError(f"Template rendering failed: {str(e)}")

    # Generate CCIE configuration
    try:
        result = CCIEConfigGenerator.generate(validated_data, template_renderer)
    except RenderError as e:
        return jsonify({
            'error': 'Rendering Error',
            'message': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'error': 'Generation Error',
            'message': str(e)
        }), 500

    # Handle different output formats
    if output_format == 'json':
        import json
        config_output = json.dumps(validated_data, indent=2)
    elif output_format == 'yaml':
        import yaml
        config_output = yaml.dump(validated_data, default_flow_style=False)
    else:
        config_output = result['cli']

    # Save to history if user is authenticated
    user_id = None
    if hasattr(g, 'current_user'):
        user_id = g.current_user['user_id']

    history_entry = ConfigHistory(
        user_id=user_id,
        platform=platform,
        hostname=validated_data.get('hostname', 'unknown'),
        generated_config=config_output,
        output_format=output_format,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        tags=validated_data.get('tags'),
        version=validated_data.get('version', 'CCIE-v1')
    )
    history_entry.set_config_data(validated_data)

    db.session.add(history_entry)
    db.session.commit()

    # Build response
    response = {
        'success': True,
        'platform': platform,
        'device_type': validated_data.get('device_type'),
        'hostname': validated_data.get('hostname'),
        'output_format': output_format,
        'configuration': config_output,
        'history_id': history_entry.id
    }

    # Include validation if requested
    if validated_data.get('generate_validation', True) and result.get('validation'):
        response['validation'] = result['validation']

    # Include explanation if requested
    if validated_data.get('generate_explanation', True) and result.get('explanation'):
        response['explanation'] = result['explanation']

    return jsonify(response), 200


@ccie_api_bp.route('/ccie-schema', methods=['GET'])
def get_ccie_schema():
    """
    Get complete CCIE schema documentation.

    Returns:
        JSON response with schema details and examples
    """
    return jsonify({
        'version': 'CCIE-v1',
        'endpoint': '/api/v1/generate-ccie',
        'method': 'POST',
        'description': 'CCIE-level configuration generator with full protocol support',

        'supported_device_types': ['switch', 'router', 'firewall'],
        'supported_platforms': ['ios', 'ios-xe', 'nxos', 'ios-xr', 'asa', 'ftd'],

        'protocol_coverage': {
            'L2': [
                'VLAN', 'STP/RSTP/MSTP/PVST', 'EtherChannel', 'LACP/PAgP',
                'VTP', 'QinQ', 'PVLAN', 'DAI', 'Port Security', 'DHCP Snooping',
                'IGMP Snooping', 'StackWise/vPC'
            ],
            'L3': [
                'Static', 'OSPFv2/v3', 'EIGRP', 'RIP', 'IS-IS', 'BGP',
                'PBR', 'VRF-Lite', 'MPLS', 'Segment Routing', 'CEF',
                'HSRP', 'VRRP', 'GLBP', 'uRPF'
            ],
            'Multicast': [
                'IGMPv1-3', 'PIM-SM/DM/SSM/BIDIR', 'MSDP', 'Auto-RP', 'Anycast-RP'
            ],
            'VPN': [
                'IPsec', 'GRE', 'DMVPN', 'FlexVPN', 'GETVPN', 'L2TP',
                'SSL VPN (AnyConnect)', 'SD-WAN'
            ],
            'Security': [
                'ACL', 'ZBFW', 'CBAC', 'ASA Policies', 'FTD NGFW',
                'IPS/IDS', 'TrustSec', '802.1X', 'DAI', 'DHCP Snooping',
                'Port Security'
            ],
            'QoS': [
                'LLQ', 'CBWFQ', 'Shaping', 'Policing', 'WRED', 'AutoQoS',
                'NBAR2', 'DSCP/CoS mapping'
            ],
            'Services': [
                'NAT/PAT', 'DHCP Server/Relay', 'DNS', 'SNMP', 'Syslog',
                'NTP', 'PTP', 'NetFlow/IPFIX', 'EEM'
            ],
            'Infrastructure': [
                'BFD', 'NSF/SSO', 'ISSU', 'Stack/Cluster', 'CoPP',
                'Smart Licensing', 'NETCONF/RESTCONF/gNMI'
            ]
        },

        'required_fields': ['device_type', 'platform', 'hostname'],

        'example_router': {
            'device_type': 'router',
            'platform': 'ios-xe',
            'hostname': 'PAR-CORE-1',
            'domain_name': 'enterprise.com',
            'loopbacks': ['10.255.0.1/32'],

            'interfaces': [
                {
                    'name': 'GigabitEthernet0/0',
                    'description': 'WAN-MPLS',
                    'ip': '172.16.0.2/30'
                },
                {
                    'name': 'GigabitEthernet0/1',
                    'description': 'LAN-CORE',
                    'ip': '10.10.0.1/24'
                }
            ],

            'routing': {
                'static': [
                    {'prefix': '0.0.0.0/0', 'next_hop': '172.16.0.1'}
                ],

                'ospf': {
                    'process_id': 100,
                    'router_id': '10.255.0.1',
                    'bfd': True,
                    'areas': [
                        {
                            'id': 0,
                            'networks': ['10.10.0.0/16', '10.20.0.0/16']
                        }
                    ]
                },

                'bgp': {
                    'asn': 65010,
                    'router_id': '10.255.0.1',
                    'neighbors': [
                        {
                            'ip': '192.0.2.1',
                            'remote_as': 65000,
                            'description': 'MPLS PE'
                        }
                    ],
                    'networks': ['10.10.0.0/16'],
                    'maximum_paths': 4
                }
            },

            'redundancy': {
                'hsrp': [
                    {
                        'interface': 'GigabitEthernet0/1',
                        'group': 10,
                        'vip': '10.10.0.254',
                        'priority': 110,
                        'version': 2
                    }
                ]
            },

            'multicast': {
                'enabled': True,
                'igmp_version': 3,
                'pim_mode': 'sparse-mode',
                'rp': {
                    'type': 'static',
                    'address': '10.255.0.10'
                }
            },

            'security': {
                'aaa': {
                    'tacacs': [
                        {'host': '10.1.1.1', 'key': 'secret123'}
                    ],
                    'local_users': {
                        'admin': 'admin_password'
                    }
                },

                'acl': [
                    {
                        'name': 'ACL-IN',
                        'type': 'extended',
                        'entries': [
                            {'action': 'permit', 'protocol': 'ip', 'source': '10.0.0.0/8'}
                        ]
                    }
                ],

                'vpn': {
                    'type': 'ipsec',
                    'ike_version': 2,
                    'peers': [
                        {
                            'peer_ip': '203.0.113.2',
                            'psk': 'vpn_secret',
                            'local_subnet': '10.10.0.0/24',
                            'remote_subnet': '10.20.0.0/24'
                        }
                    ]
                }
            },

            'nat': {
                'inside': 'GigabitEthernet0/1',
                'outside': 'GigabitEthernet0/0',
                'rules': [
                    {'source': '10.10.0.0/24', 'action': 'overload'}
                ]
            },

            'qos': {
                'enabled': True,
                'classes': [
                    {
                        'name': 'VOICE',
                        'dscp': 'dscp ef',
                        'priority': 'strict'
                    },
                    {
                        'name': 'CRITICAL',
                        'dscp': 'dscp af31',
                        'bandwidth': '30%'
                    }
                ]
            },

            'services': {
                'ntp': ['192.0.2.10', '192.0.2.11'],
                'dns': ['8.8.8.8'],
                'syslog': ['10.255.1.10'],
                'snmp': {
                    'version': 3,
                    'users': ['netmon'],
                    'location': 'Paris DC1',
                    'contact': 'netops@enterprise.com'
                },
                'netflow': True
            },

            'output_format': 'cli',
            'generate_validation': True,
            'generate_explanation': True
        },

        'features': {
            'validation': 'Comprehensive validation of all parameters',
            'explanation': 'CCIE-level technical explanation of configuration',
            'best_practices': 'Automatic application of Cisco best practices',
            'security_hardening': 'Built-in security hardening (CoPP, SSH, AAA)',
            'comments': 'Fully commented configuration blocks',
            'hierarchical': 'Proper Cisco IOS hierarchy and structure'
        }
    }), 200


@ccie_api_bp.route('/ccie-examples', methods=['GET'])
def get_ccie_examples():
    """Get CCIE configuration examples for different scenarios."""
    return jsonify({
        'examples': {
            'enterprise_router': 'Full-featured enterprise edge router',
            'data_center_switch': 'NX-OS data center switch with VxLAN',
            'firewall_dmz': 'ASA firewall with DMZ and VPN',
            'service_provider_pe': 'IOS-XR service provider PE router',
            'campus_core': 'Campus core with OSPF, HSRP, QoS'
        },
        'download_url': '/api/v1/ccie-examples/<example_name>',
        'note': 'Use example configurations as templates for your deployments'
    }), 200
