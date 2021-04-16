from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    if settings.USE_AWS:
        location = settings.AWS_STATIC_LOCATION
    else:
        pass


class PublicMediaStorage(S3Boto3Storage):
    if settings.USE_AWS:
        location = settings.AWS_PUBLIC_MEDIA_LOCATION
        file_overwrite = True
        default_acl = 'public-read'
    else:
        pass
