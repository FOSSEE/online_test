from __future__ import absolute_import, unicode_literals

# Import celery only if available (for deployments without Celery worker)
try:
    from online_test.celery_settings import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not available, skip it
    __all__ = ()
    celery_app = None

__version__ = '0.31.1'
