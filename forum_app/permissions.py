from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Nur Author oder Admin dürfen schreiben/löschen, sonst nur lesen."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff
