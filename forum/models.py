import uuid
import os

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)


def validate_image(image):
    file_size = image.file.size
    limit_mb = 30
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError("Max size of file is {0} MB".format(limit_mb))


def get_image_dir(instance, filename):
    return os.sep.join((
        'post_%s' % (instance.uid), filename
    ))


class ForumBase(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to=get_image_dir, blank=True,
                              null=True, validators=[validate_image])
    active = models.BooleanField(default=True)
    anonymous = models.BooleanField(default=False)


class Post(ForumBase):
    title = models.CharField(max_length=200)
    target_ct = models.ForeignKey(ContentType,
                                  blank=True,
                                  null=True,
                                  related_name='target_obj',
                                  on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True,
                                            blank=True,
                                            db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')

    def __str__(self):
        return self.title

    def get_last_comment(self):
        if self.comments.exists():
            return self.comments.filter(active=True).last()

    def get_comments_count(self):
        if self.comments.exists():
            return self.comments.filter(active=True).count()


class Comment(ForumBase):
    post_field = models.ForeignKey(Post, on_delete=models.CASCADE,
                                   related_name='comments')

    def __str__(self):
        return 'Comment by {0}: {1}'.format(self.creator.username,
                                            self.post_field.title)