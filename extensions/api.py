"""
REST API Blueprint - v1
Provides /api/v1/generate endpoint for configuration generation.
"""
from flask import Blueprint, request, jsonify, current_app, g
from marshmallow import Schema, fields, validate, ValidationError as MarshmallowValidationError
from models import db, ConfigHistory
from utils.validators import validate_config_data, ValidationError
from utils.auth import auth_required, optional_auth
from utils.renderer import render_config, RenderError


api_bp = Blueprint('api', __name__)


# Marshmallow schemas for API validation
class OSPFNetworkSchema(Schema):
    """OSPF network schema."""
    network = fields.Str(required=True)
    wildcard = fields.Str(required=True)
    area = fields.Int(required=True)


class OSPFSchema(Schema):
    """OSPF configuration schema."""
    enabled = fields.Bool(required=False, load_default=False)
    process_id = fields.Int(required=False)
    router_id = fields.Str(required=False)
    networks = fields.List(fields.Nested(OSPFNetworkSchema), required=False)


class StaticRouteSchema(Schema):
    """Static route schema."""
    network = fields.Str(required=True)
    mask = fields.Str(required=False)
    next_hop = fields.Str(required=True)
    distance = fields.Int(required=False, validate=validate.Range(min=1, max=255))


class VLANSchema(Schema):
    """VLAN schema."""
    id = fields.Int(required=True, validate=validate.Range(min=1, max=4094))
    name = fields.Str(required=True)
    description = fields.Str(required=False)


class InterfaceSchema(Schema):
    """Interface schema."""
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    ip_address = fields.Str(required=False)
    subnet_mask = fields.Str(required=False)
    enabled = fields.Bool(required=False, load_default=True)
    vlan = fields.Int(required=False)


class TacacsServerSchema(Schema):
    """TACACS+ server schema."""
    host = fields.Str(required=True)
    key = fields.Str(required=False)
    port = fields.Int(required=False, validate=validate.Range(min=1, max=65535))


class AAASchema(Schema):
    """AAA configuration schema."""
    tacacs_servers = fields.List(fields.Nested(TacacsServerSchema), required=False)
    radius_servers = fields.List(fields.Str(), required=False)
    local_users = fields.Dict(required=False)


class ConfigGenerateSchema(Schema):
    """Main configuration generation request schema."""
    platform = fields.Str(
        required=True,
        validate=validate.OneOf(['ios', 'nxos', 'asa', 'iosxr'])
    )
    hostname = fields.Str(required=True, validate=validate.Length(min=1, max=63))
    domain_name = fields.Str(required=False)
    enable_secret = fields.Str(required=False)

    # Interfaces
    interfaces = fields.List(fields.Nested(InterfaceSchema), required=False)

    # VLANs
    vlans = fields.List(fields.Nested(VLANSchema), required=False)

    # Routing
    static_routes = fields.List(fields.Nested(StaticRouteSchema), required=False)
    ospf = fields.Nested(OSPFSchema, required=False)

    # Services
    ntp_servers = fields.List(fields.Str(), required=False)
    dns_servers = fields.List(fields.Str(), required=False)
    syslog_servers = fields.List(fields.Str(), required=False)

    # AAA
    aaa = fields.Nested(AAASchema, required=False)

    # Banners
    banner_motd = fields.Str(required=False)
    banner_login = fields.Str(required=False)

    # SNMP
    snmp_community = fields.Str(required=False)
    snmp_location = fields.Str(required=False)
    snmp_contact = fields.Str(required=False)

    # Output format
    output_format = fields.Str(
        required=False,
        load_default='cli',
        validate=validate.OneOf(['cli', 'json', 'yaml'])
    )

    # Metadata
    tags = fields.Str(required=False)
    version = fields.Str(required=False)


@api_bp.route('/generate', methods=['POST'])
@optional_auth
def generate_config():
    """
    Generate device configuration.

    Request body should contain configuration parameters as JSON.

    Returns:
        JSON response with generated configuration
    """
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()

    # Validate with Marshmallow
    schema = ConfigGenerateSchema()
    try:
        validated_data = schema.load(data)
    except MarshmallowValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'details': e.messages
        }), 400

    # Additional custom validation
    try:
        validate_config_data(
            validated_data,
            current_app.config['SUPPORTED_PLATFORMS']
        )
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': str(e)
        }), 400

    # Extract output format
    output_format = validated_data.pop('output_format', 'cli')
    platform = validated_data['platform']

    # Render configuration
    try:
        generated_config = render_config(
            platform=platform,
            config_data=validated_data,
            output_format=output_format
        )
    except RenderError as e:
        return jsonify({
            'error': 'Rendering Error',
            'message': str(e)
        }), 500

    # Save to history if user is authenticated
    user_id = None
    if hasattr(g, 'current_user'):
        user_id = g.current_user['user_id']

    history_entry = ConfigHistory(
        user_id=user_id,
        platform=platform,
        hostname=validated_data.get('hostname', 'unknown'),
        generated_config=generated_config,
        output_format=output_format,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        tags=validated_data.get('tags'),
        version=validated_data.get('version')
    )
    history_entry.set_config_data(validated_data)

    db.session.add(history_entry)
    db.session.commit()

    response = {
        'success': True,
        'platform': platform,
        'hostname': validated_data.get('hostname'),
        'output_format': output_format,
        'configuration': generated_config,
        'history_id': history_entry.id
    }

    return jsonify(response), 200


@api_bp.route('/validate', methods=['POST'])
def validate_config():
    """
    Validate configuration data without generating output.

    Returns:
        JSON response with validation results
    """
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()

    # Validate with Marshmallow
    schema = ConfigGenerateSchema()
    try:
        validated_data = schema.load(data)
    except MarshmallowValidationError as e:
        return jsonify({
            'valid': False,
            'error': 'Schema Validation Error',
            'details': e.messages
        }), 200  # Return 200 but indicate validation failed

    # Additional custom validation
    try:
        validate_config_data(
            validated_data,
            current_app.config['SUPPORTED_PLATFORMS']
        )
    except ValidationError as e:
        return jsonify({
            'valid': False,
            'error': 'Data Validation Error',
            'message': str(e)
        }), 200

    return jsonify({
        'valid': True,
        'message': 'Configuration data is valid',
        'platform': validated_data['platform'],
        'hostname': validated_data.get('hostname')
    }), 200


@api_bp.route('/platforms', methods=['GET'])
def list_platforms():
    """
    List supported platforms.

    Returns:
        JSON response with platform list
    """
    return jsonify({
        'platforms': current_app.config['SUPPORTED_PLATFORMS']
    }), 200


@api_bp.route('/schema', methods=['GET'])
def get_schema():
    """
    Get API schema documentation.

    Returns:
        JSON response with schema details
    """
    schema = ConfigGenerateSchema()

    return jsonify({
        'version': 'v1',
        'endpoint': '/api/v1/generate',
        'method': 'POST',
        'content_type': 'application/json',
        'schema': {
            'required_fields': ['platform', 'hostname'],
            'supported_platforms': current_app.config['SUPPORTED_PLATFORMS'],
            'output_formats': current_app.config['OUTPUT_FORMATS'],
            'optional_fields': [
                'domain_name', 'enable_secret', 'interfaces', 'vlans',
                'static_routes', 'ospf', 'ntp_servers', 'dns_servers',
                'syslog_servers', 'aaa', 'banner_motd', 'banner_login',
                'snmp_community', 'snmp_location', 'snmp_contact', 'tags', 'version'
            ]
        },
        'example': {
            'platform': 'ios',
            'hostname': 'router01',
            'domain_name': 'example.com',
            'interfaces': [
                {
                    'name': 'GigabitEthernet0/0',
                    'ip_address': '192.168.1.1',
                    'subnet_mask': '255.255.255.0',
                    'description': 'LAN Interface'
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
    }), 200
