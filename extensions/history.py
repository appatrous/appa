"""
Configuration History Blueprint
Provides endpoints for viewing and managing configuration history.
"""
from flask import Blueprint, request, jsonify, g
from sqlalchemy import desc
from datetime import datetime, timedelta
from models import db, ConfigHistory
from utils.auth import auth_required, admin_required


history_bp = Blueprint('history', __name__)


@history_bp.route('/list', methods=['GET'])
@auth_required
def list_history():
    """
    List configuration history for the authenticated user.

    Query parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - platform: Filter by platform
        - hostname: Filter by hostname
        - days: Filter by days back (default: 30)

    Returns:
        JSON response with history list
    """
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Max 100 per page

    # Filters
    platform = request.args.get('platform')
    hostname = request.args.get('hostname')
    days = request.args.get('days', 30, type=int)

    # Build query
    query = ConfigHistory.query

    # Filter by user (non-admin users only see their own)
    if not g.current_user['is_admin']:
        query = query.filter_by(user_id=g.current_user['user_id'])

    # Date filter
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(ConfigHistory.created_at >= cutoff_date)

    # Platform filter
    if platform:
        query = query.filter_by(platform=platform.lower())

    # Hostname filter
    if hostname:
        query = query.filter(ConfigHistory.hostname.ilike(f'%{hostname}%'))

    # Order by creation date
    query = query.order_by(desc(ConfigHistory.created_at))

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'items': [item.to_dict() for item in pagination.items]
    }), 200


@history_bp.route('/<int:history_id>', methods=['GET'])
@auth_required
def get_history(history_id):
    """
    Get specific configuration history entry.

    Args:
        history_id: History entry ID

    Returns:
        JSON response with configuration details
    """
    history = ConfigHistory.query.get(history_id)

    if not history:
        return jsonify({
            'error': 'Not Found',
            'message': 'History entry not found'
        }), 404

    # Check authorization (non-admin users can only view their own)
    if not g.current_user['is_admin'] and history.user_id != g.current_user['user_id']:
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to view this entry'
        }), 403

    return jsonify({
        'success': True,
        'history': history.to_dict(include_config=True)
    }), 200


@history_bp.route('/<int:history_id>/download', methods=['GET'])
@auth_required
def download_config(history_id):
    """
    Download configuration as plain text file.

    Args:
        history_id: History entry ID

    Returns:
        Plain text configuration file
    """
    history = ConfigHistory.query.get(history_id)

    if not history:
        return jsonify({
            'error': 'Not Found',
            'message': 'History entry not found'
        }), 404

    # Check authorization
    if not g.current_user['is_admin'] and history.user_id != g.current_user['user_id']:
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to download this entry'
        }), 403

    # Generate filename
    timestamp = history.created_at.strftime('%Y%m%d_%H%M%S')
    filename = f"{history.hostname}_{history.platform}_{timestamp}.txt"

    from flask import Response
    return Response(
        history.generated_config,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@history_bp.route('/<int:history_id>', methods=['DELETE'])
@auth_required
def delete_history(history_id):
    """
    Delete configuration history entry.

    Args:
        history_id: History entry ID

    Returns:
        JSON response with deletion confirmation
    """
    history = ConfigHistory.query.get(history_id)

    if not history:
        return jsonify({
            'error': 'Not Found',
            'message': 'History entry not found'
        }), 404

    # Check authorization (non-admin users can only delete their own)
    if not g.current_user['is_admin'] and history.user_id != g.current_user['user_id']:
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to delete this entry'
        }), 403

    db.session.delete(history)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'History entry deleted successfully'
    }), 200


@history_bp.route('/stats', methods=['GET'])
@auth_required
def get_stats():
    """
    Get configuration generation statistics.

    Returns:
        JSON response with statistics
    """
    # Build query based on user role
    if g.current_user['is_admin']:
        query = ConfigHistory.query
    else:
        query = ConfigHistory.query.filter_by(user_id=g.current_user['user_id'])

    # Total configurations
    total = query.count()

    # By platform
    from sqlalchemy import func
    platform_stats = db.session.query(
        ConfigHistory.platform,
        func.count(ConfigHistory.id)
    ).group_by(ConfigHistory.platform)

    if not g.current_user['is_admin']:
        platform_stats = platform_stats.filter_by(user_id=g.current_user['user_id'])

    platform_counts = {platform: count for platform, count in platform_stats.all()}

    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = query.filter(ConfigHistory.created_at >= week_ago).count()

    return jsonify({
        'success': True,
        'stats': {
            'total_configs': total,
            'by_platform': platform_counts,
            'last_7_days': recent_count
        }
    }), 200


@history_bp.route('/cleanup', methods=['POST'])
@admin_required
def cleanup_old_history():
    """
    Clean up old history entries (admin only).

    Request body:
        - days: Number of days to keep (default: from config)

    Returns:
        JSON response with cleanup results
    """
    from flask import current_app

    data = request.get_json() or {}
    days = data.get('days', current_app.config['HISTORY_RETENTION_DAYS'])

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Delete old entries
    deleted = ConfigHistory.query.filter(
        ConfigHistory.created_at < cutoff_date
    ).delete()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Deleted {deleted} old history entries',
        'deleted_count': deleted,
        'retention_days': days
    }), 200


@history_bp.route('/compare', methods=['POST'])
@auth_required
def compare_configs():
    """
    Compare two configuration history entries with detailed diff.

    Request body:
        - config1_id: First configuration ID
        - config2_id: Second configuration ID
        - diff_type: Type of diff (unified, html, structured) - default: structured

    Returns:
        JSON response with detailed comparison
    """
    from utils.diff import generate_change_summary, ConfigDiff

    data = request.get_json()

    if not data or 'config1_id' not in data or 'config2_id' not in data:
        return jsonify({
            'error': 'Bad Request',
            'message': 'config1_id and config2_id are required'
        }), 400

    config1 = ConfigHistory.query.get(data['config1_id'])
    config2 = ConfigHistory.query.get(data['config2_id'])

    if not config1 or not config2:
        return jsonify({
            'error': 'Not Found',
            'message': 'One or both configurations not found'
        }), 404

    # Check authorization
    if not g.current_user['is_admin']:
        if config1.user_id != g.current_user['user_id'] or \
           config2.user_id != g.current_user['user_id']:
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to compare these entries'
            }), 403

    # Get diff type
    diff_type = data.get('diff_type', 'structured')

    # Generate comparison
    filename1 = f"{config1.hostname} ({config1.platform})"
    filename2 = f"{config2.hostname} ({config2.platform})"

    if diff_type == 'html':
        diff_content = ConfigDiff.html_diff(
            config1.generated_config,
            config2.generated_config,
            filename1,
            filename2
        )
        return diff_content, 200, {'Content-Type': 'text/html'}

    summary = generate_change_summary(
        config1.generated_config,
        config2.generated_config,
        filename1,
        filename2
    )

    return jsonify({
        'success': True,
        'config1': {
            'id': config1.id,
            'hostname': config1.hostname,
            'platform': config1.platform,
            'created_at': config1.created_at.isoformat() if config1.created_at else None
        },
        'config2': {
            'id': config2.id,
            'hostname': config2.hostname,
            'platform': config2.platform,
            'created_at': config2.created_at.isoformat() if config2.created_at else None
        },
        'comparison': summary
    }), 200
