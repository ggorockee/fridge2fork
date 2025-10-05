"""
Core views for health checks and system status
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import datetime


def health_check(request):
    """
    Health check endpoint for K8s liveness and readiness probes

    Returns:
        - 200 OK: All systems operational
        - 503 Service Unavailable: System issues detected
    """
    status = {
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'checks': {}
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = 'ok'
    except Exception as e:
        status['status'] = 'unhealthy'
        status['checks']['database'] = f'error: {str(e)}'
        return JsonResponse(status, status=503)

    # Check cache (optional, if using Redis)
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            status['checks']['cache'] = 'ok'
        else:
            status['checks']['cache'] = 'warning: cache not working'
    except Exception as e:
        status['checks']['cache'] = f'warning: {str(e)}'

    return JsonResponse(status)


def readiness_check(request):
    """
    Readiness check - checks if app is ready to serve traffic
    """
    # For now, same as health check
    return health_check(request)


def liveness_check(request):
    """
    Liveness check - checks if app is alive (simpler than health check)
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': datetime.datetime.now().isoformat()
    })
