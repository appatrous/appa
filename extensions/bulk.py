"""
Bulk operations blueprint for batch configuration generation.
Supports CSV import and bulk processing.
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import csv
import io
import json
from models import db, ConfigHistory
from utils.auth import auth_required
from utils.validators import validate_config_data
from utils.renderer import render_template
import tempfile
import zipfile
from datetime import datetime

bulk_bp = Blueprint('bulk', __name__)


def parse_csv_to_configs(csv_content: str) -> list:
    """
    Parse CSV content to configuration list.

    CSV Format:
        platform,hostname,domain_name,interface_name,interface_ip,interface_mask,...

    Args:
        csv_content: CSV file content

    Returns:
        List of configuration dictionaries

    Raises:
        ValueError: If CSV format is invalid
    """
    configs = []
    reader = csv.DictReader(io.StringIO(csv_content))

    for row_num, row in enumerate(reader, start=2):
        try:
            # Build configuration from CSV row
            config = {
                'platform': row.get('platform', '').strip(),
                'hostname': row.get('hostname', '').strip(),
                'domain_name': row.get('domain_name', '').strip(),
                'output_format': row.get('output_format', 'cli').strip()
            }

            # Parse interfaces (supports multiple interfaces)
            interfaces = []
            for i in range(1, 11):  # Support up to 10 interfaces
                name_key = f'interface_{i}_name'
                ip_key = f'interface_{i}_ip'
                mask_key = f'interface_{i}_mask'
                desc_key = f'interface_{i}_description'

                if name_key in row and row.get(name_key):
                    interface = {
                        'name': row.get(name_key, '').strip(),
                        'ip_address': row.get(ip_key, '').strip(),
                        'subnet_mask': row.get(mask_key, '').strip(),
                        'description': row.get(desc_key, '').strip()
                    }
                    interfaces.append(interface)

            if interfaces:
                config['interfaces'] = interfaces

            # Parse VLANs
            vlans = []
            for i in range(1, 11):  # Support up to 10 VLANs
                id_key = f'vlan_{i}_id'
                name_key = f'vlan_{i}_name'

                if id_key in row and row.get(id_key):
                    vlan = {
                        'id': int(row.get(id_key)),
                        'name': row.get(name_key, '').strip()
                    }
                    vlans.append(vlan)

            if vlans:
                config['vlans'] = vlans

            # Parse static routes
            routes = []
            for i in range(1, 6):  # Support up to 5 routes
                network_key = f'route_{i}_network'
                nexthop_key = f'route_{i}_nexthop'

                if network_key in row and row.get(network_key):
                    route = {
                        'network': row.get(network_key, '').strip(),
                        'next_hop': row.get(nexthop_key, '').strip()
                    }
                    routes.append(route)

            if routes:
                config['static_routes'] = routes

            # Optional fields
            if row.get('enable_secret'):
                config['enable_secret'] = row.get('enable_secret').strip()

            if row.get('ntp_servers'):
                config['ntp_servers'] = [s.strip() for s in row.get('ntp_servers').split(',')]

            if row.get('dns_servers'):
                config['dns_servers'] = [s.strip() for s in row.get('dns_servers').split(',')]

            if row.get('syslog_servers'):
                config['syslog_servers'] = [s.strip() for s in row.get('syslog_servers').split(',')]

            configs.append({
                'row': row_num,
                'config': config
            })

        except Exception as e:
            raise ValueError(f"Error parsing row {row_num}: {str(e)}")

    return configs


@bulk_bp.route('/upload', methods=['POST'])
@auth_required
def upload_csv():
    """
    Upload CSV file for bulk configuration generation.

    Form Data:
        file: CSV file
        validate_only: If true, only validate without generating (optional)

    Returns:
        JSON response with validation results or generated configs
    """
    if 'file' not in request.files:
        return jsonify({
            'error': 'Bad Request',
            'message': 'No file provided'
        }), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({
            'error': 'Bad Request',
            'message': 'No file selected'
        }), 400

    if not file.filename.endswith('.csv'):
        return jsonify({
            'error': 'Bad Request',
            'message': 'File must be a CSV'
        }), 400

    # Read CSV content
    try:
        csv_content = file.read().decode('utf-8')
    except UnicodeDecodeError:
        return jsonify({
            'error': 'Bad Request',
            'message': 'File must be UTF-8 encoded'
        }), 400

    # Parse CSV
    try:
        configs = parse_csv_to_configs(csv_content)
    except ValueError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': str(e)
        }), 400

    # Validate all configurations
    validation_errors = []
    for item in configs:
        try:
            validate_config_data(item['config'])
        except Exception as e:
            validation_errors.append({
                'row': item['row'],
                'error': str(e)
            })

    if validation_errors:
        return jsonify({
            'error': 'Validation Failed',
            'message': f'{len(validation_errors)} configuration(s) failed validation',
            'errors': validation_errors,
            'total_configs': len(configs)
        }), 400

    # If validate_only, return validation results
    validate_only = request.form.get('validate_only', 'false').lower() == 'true'
    if validate_only:
        return jsonify({
            'success': True,
            'message': 'All configurations are valid',
            'total_configs': len(configs)
        })

    # Generate configurations
    results = []
    for item in configs:
        try:
            config_data = item['config']
            platform = config_data['platform']

            # Render configuration
            rendered_config = render_template(platform, config_data)

            # Save to history
            history_entry = ConfigHistory(
                user_id=request.current_user_id,
                platform=platform,
                hostname=config_data.get('hostname', 'unknown'),
                config_data=json.dumps(config_data),
                generated_config=rendered_config,
                output_format=config_data.get('output_format', 'cli'),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )

            db.session.add(history_entry)
            db.session.flush()

            results.append({
                'row': item['row'],
                'hostname': config_data.get('hostname'),
                'platform': platform,
                'history_id': history_entry.id,
                'success': True
            })

        except Exception as e:
            results.append({
                'row': item['row'],
                'hostname': config_data.get('hostname', 'unknown'),
                'success': False,
                'error': str(e)
            })

    db.session.commit()

    success_count = sum(1 for r in results if r['success'])
    failure_count = len(results) - success_count

    return jsonify({
        'success': True,
        'message': f'Generated {success_count} configurations, {failure_count} failed',
        'total': len(results),
        'success_count': success_count,
        'failure_count': failure_count,
        'results': results
    })


@bulk_bp.route('/download', methods=['POST'])
@auth_required
def download_bulk():
    """
    Download multiple configurations as ZIP.

    Request Body:
        config_ids: List of configuration history IDs

    Returns:
        ZIP file with configurations
    """
    data = request.get_json()

    if not data or 'config_ids' not in data:
        return jsonify({
            'error': 'Bad Request',
            'message': 'config_ids list is required'
        }), 400

    config_ids = data['config_ids']

    if not isinstance(config_ids, list) or not config_ids:
        return jsonify({
            'error': 'Bad Request',
            'message': 'config_ids must be a non-empty list'
        }), 400

    # Fetch configurations
    configs = ConfigHistory.query.filter(ConfigHistory.id.in_(config_ids)).all()

    if not configs:
        return jsonify({
            'error': 'Not Found',
            'message': 'No configurations found'
        }), 404

    # Create ZIP file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for config in configs:
            # Generate filename
            timestamp = config.created_at.strftime('%Y%m%d_%H%M%S') if config.created_at else 'unknown'
            filename = f"{config.hostname}_{config.platform}_{timestamp}.txt"

            # Add to ZIP
            zip_file.writestr(filename, config.generated_config)

    zip_buffer.seek(0)

    # Return ZIP file
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'cisco_configs_{timestamp}.zip'
    )


@bulk_bp.route('/template', methods=['GET'])
def download_template():
    """
    Download CSV template for bulk import.

    Returns:
        CSV template file
    """
    template_data = [
        {
            'platform': 'ios',
            'hostname': 'router01',
            'domain_name': 'example.com',
            'output_format': 'cli',
            'enable_secret': 'cisco123',
            'interface_1_name': 'GigabitEthernet0/0',
            'interface_1_ip': '192.168.1.1',
            'interface_1_mask': '255.255.255.0',
            'interface_1_description': 'LAN Interface',
            'interface_2_name': 'GigabitEthernet0/1',
            'interface_2_ip': '10.0.0.1',
            'interface_2_mask': '255.255.255.0',
            'interface_2_description': 'WAN Interface',
            'vlan_1_id': '10',
            'vlan_1_name': 'DATA',
            'vlan_2_id': '20',
            'vlan_2_name': 'VOICE',
            'route_1_network': '0.0.0.0/0',
            'route_1_nexthop': '10.0.0.254',
            'ntp_servers': 'pool.ntp.org,time.nist.gov',
            'dns_servers': '8.8.8.8,8.8.4.4',
            'syslog_servers': '192.168.1.100'
        }
    ]

    # Create CSV
    output = io.StringIO()
    if template_data:
        writer = csv.DictWriter(output, fieldnames=template_data[0].keys())
        writer.writeheader()
        writer.writerows(template_data)

    csv_content = output.getvalue()

    return send_file(
        io.BytesIO(csv_content.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='cisco_config_template.csv'
    )


@bulk_bp.route('/stats', methods=['GET'])
@auth_required
def bulk_stats():
    """
    Get bulk operation statistics.

    Returns:
        JSON response with statistics
    """
    from sqlalchemy import func
    from datetime import timedelta

    # Total configurations by platform
    platform_stats = db.session.query(
        ConfigHistory.platform,
        func.count(ConfigHistory.id).label('count')
    ).filter_by(
        user_id=request.current_user_id
    ).group_by(ConfigHistory.platform).all()

    # Recent bulk operations (last 30 days)
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    recent_count = ConfigHistory.query.filter(
        ConfigHistory.user_id == request.current_user_id,
        ConfigHistory.created_at >= cutoff_date
    ).count()

    return jsonify({
        'by_platform': [{'platform': p, 'count': c} for p, c in platform_stats],
        'recent_30_days': recent_count,
        'total_configs': sum(c for _, c in platform_stats)
    })
