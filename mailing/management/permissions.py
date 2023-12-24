from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """ Restrict communication to everyone except the object owner and administrator """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class MessageIsOwnerOrReadOnly(permissions.BasePermission):
    """ Restrict communication to everyone except the object owner """
    def has_object_permission(self, request, view, obj):
        print(obj.mailing.user_id)
        if obj.mailing.user_id == request.user.id:
            return True
        return False

