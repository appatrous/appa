"""
Audit logging blueprint and utilities.
Provides endpoints for viewing and managing audit logs.
"""
from flask import Blueprint, request, jsonify
from models import db, AuditLog
from utils.auth import auth_required, admin_required
from datetime import datetime, timedelta

audit_bp = Blueprint('audit', __name__)


def log_audit_event(
    action: str,
    resource_type: str = None,
    resource_id: int = None,
    details: dict = None,
    user_id: int = None,
    status: str = 'success',
    severity: str = 'info'
):
    """
    Create an audit log entry.

    Args:
        action: Action performed (e.g., 'login', 'create_config', 'delete_user')
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        details: Additional details as dictionary
        user_id: User ID performing the action
        status: Status of the action (success, failure, error)
        severity: Severity level (info, warning, error, critical)

    Returns:
        AuditLog: Created audit log entry
    """
    audit_log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        status=status,
        severity=severity,
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent') if request else None
    )

    if details:
        audit_log.set_details(details)

    db.session.add(audit_log)
    db.session.commit()

    return audit_log


@audit_bp.route('/list', methods=['GET'])
@auth_required
@admin_required
def list_audit_logs():
    """
    List audit logs with filtering and pagination.

    Query Parameters:
        page: Page number (default 1)
        per_page: Items per page (default 50, max 100)
        action: Filter by action
        user_id: Filter by user ID
        resource_type: Filter by resource type
        severity: Filter by severity
        start_date: Start date (ISO format)
        end_date: End date (ISO format)

    Returns:
        JSON response with audit logs
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)

    # Build query
    query = AuditLog.query

    # Apply filters
    if action := request.args.get('action'):
        query = query.filter_by(action=action)

    if user_id := request.args.get('user_id', type=int):
        query = query.filter_by(user_id=user_id)

    if resource_type := request.args.get('resource_type'):
        query = query.filter_by(resource_type=resource_type)

    if severity := request.args.get('severity'):
        query = query.filter_by(severity=severity)

    if start_date := request.args.get('start_date'):
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400

    if end_date := request.args.get('end_date'):
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400

    # Order by timestamp descending
    query = query.order_by(AuditLog.timestamp.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@audit_bp.route('/<int:log_id>', methods=['GET'])
@auth_required
@admin_required
def get_audit_log(log_id):
    """
    Get specific audit log entry.

    Args:
        log_id: Audit log ID

    Returns:
        JSON response with audit log details
    """
    audit_log = AuditLog.query.get_or_404(log_id)
    return jsonify(audit_log.to_dict())


@audit_bp.route('/stats', methods=['GET'])
@auth_required
@admin_required
def audit_stats():
    """
    Get audit log statistics.

    Query Parameters:
        days: Number of days to analyze (default 7)

    Returns:
        JSON response with statistics
    """
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Total logs
    total_logs = AuditLog.query.filter(AuditLog.timestamp >= start_date).count()

    # Logs by action
    from sqlalchemy import func
    action_stats = db.session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date
    ).group_by(AuditLog.action).all()

    # Logs by severity
    severity_stats = db.session.query(
        AuditLog.severity,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date
    ).group_by(AuditLog.severity).all()

    # Failed actions
    failed_count = AuditLog.query.filter(
        AuditLog.timestamp >= start_date,
        AuditLog.status == 'failure'
    ).count()

    # Top users
    top_users = db.session.query(
        AuditLog.user_id,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date,
        AuditLog.user_id.isnot(None)
    ).group_by(AuditLog.user_id).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()

    return jsonify({
        'period_days': days,
        'start_date': start_date.isoformat(),
        'total_logs': total_logs,
        'failed_actions': failed_count,
        'by_action': [{'action': a, 'count': c} for a, c in action_stats],
        'by_severity': [{'severity': s, 'count': c} for s, c in severity_stats],
        'top_users': [{'user_id': u, 'count': c} for u, c in top_users]
    })


@audit_bp.route('/cleanup', methods=['POST'])
@auth_required
@admin_required
def cleanup_old_logs():
    """
    Delete old audit logs.

    Request Body:
        days: Keep logs from last N days (default 90)

    Returns:
        JSON response with cleanup results
    """
    data = request.get_json() or {}
    days = data.get('days', 90)

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    deleted_count = AuditLog.query.filter(
        AuditLog.timestamp < cutoff_date
    ).delete()

    db.session.commit()

    # Log the cleanup action
    log_audit_event(
        action='cleanup_audit_logs',
        resource_type='audit_log',
        details={'days': days, 'deleted_count': deleted_count},
        user_id=request.current_user_id,
        severity='warning'
    )

    return jsonify({
        'message': f'Deleted {deleted_count} audit log entries older than {days} days',
        'deleted_count': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    })


@audit_bp.route('/export', methods=['GET'])
@auth_required
@admin_required
def export_audit_logs():
    """
    Export audit logs as JSON.

    Query Parameters:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        format: Export format (json or csv, default json)

    Returns:
        JSON or CSV file with audit logs
    """
    import csv
    import io

    query = AuditLog.query

    if start_date := request.args.get('start_date'):
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400

    if end_date := request.args.get('end_date'):
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400

    logs = query.order_by(AuditLog.timestamp.desc()).all()

    export_format = request.args.get('format', 'json').lower()

    if export_format == 'csv':
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Timestamp', 'User ID', 'Username', 'Action',
            'Resource Type', 'Resource ID', 'Status', 'Severity',
            'IP Address', 'User Agent'
        ])

        # Write data
        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.isoformat(),
                log.user_id,
                log.user.username if log.user else 'anonymous',
                log.action,
                log.resource_type,
                log.resource_id,
                log.status,
                log.severity,
                log.ip_address,
                log.user_agent
            ])

        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=audit_logs_{datetime.utcnow().strftime("%Y%m%d")}.csv'
            }
        )
    else:
        # Return JSON
        return jsonify({
            'logs': [log.to_dict() for log in logs],
            'total': len(logs)
        })


# Helper functions for common audit events

def log_login_attempt(username: str, success: bool, user_id: int = None):
    """Log login attempt."""
    return log_audit_event(
        action='login',
        resource_type='user',
        resource_id=user_id,
        details={'username': username},
        user_id=user_id,
        status='success' if success else 'failure',
        severity='info' if success else 'warning'
    )


def log_logout(user_id: int):
    """Log logout."""
    return log_audit_event(
        action='logout',
        resource_type='user',
        user_id=user_id,
        status='success'
    )


def log_config_generation(user_id: int, platform: str, hostname: str, config_id: int):
    """Log configuration generation."""
    return log_audit_event(
        action='generate_config',
        resource_type='config',
        resource_id=config_id,
        details={'platform': platform, 'hostname': hostname},
        user_id=user_id,
        status='success'
    )


def log_api_key_creation(user_id: int, key_id: int, key_name: str):
    """Log API key creation."""
    return log_audit_event(
        action='create_api_key',
        resource_type='api_key',
        resource_id=key_id,
        details={'name': key_name},
        user_id=user_id,
        severity='warning'
    )


def log_api_key_deletion(user_id: int, key_id: int, key_name: str):
    """Log API key deletion."""
    return log_audit_event(
        action='delete_api_key',
        resource_type='api_key',
        resource_id=key_id,
        details={'name': key_name},
        user_id=user_id,
        severity='warning'
    )


def log_security_event(event_type: str, details: dict, severity: str = 'error'):
    """Log security event."""
    return log_audit_event(
        action=f'security_{event_type}',
        resource_type='security',
        details=details,
        status='error',
        severity=severity
    )
