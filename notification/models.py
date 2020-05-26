from django.db import models
from django.contrib.auth.models import User

from yaksh.models import Course


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name='subscribe')
    subscribe = models.BooleanField(default=True)

    def __str__(self):
        return '{0}: {1}: {2}'.format(self.user, self.course, self.subscribe)
