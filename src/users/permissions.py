from rest_framework import permissions

class IsNotAutoexcluido(permissions.BasePermission):
    def has_permission(self, request, view):
        return not request.user.esta_autoexcluido