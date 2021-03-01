from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    location = settings.AWS_STATIC_LOCATION if settings.USE_AWS else settings.STATIC_URL


class PublicMediaStorage(S3Boto3Storage):
    location = settings.AWS_PUBLIC_MEDIA_LOCATION if settings.USE_AWS else settings.MEDIA_URL
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    location = settings.AWS_PRIVATE_MEDIA_LOCATION if settings.USE_AWS else settings.MEDIA_URL
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False