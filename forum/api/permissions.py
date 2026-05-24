from rest_framework import permissions

from yaksh.models import Course


class IsAuthorOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # write permissions are only allowed to the author of a post
        return obj.creator == request.user
