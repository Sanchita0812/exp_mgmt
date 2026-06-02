from rest_framework.permissions import BasePermission

class IsEmployee(BasePermission):

    def has_permission(self, request, view):

        return request.user.role == 'EMPLOYEE'

class IsManager(BasePermission):

    def has_permission(self, request, view):

        return request.user.role == 'MANAGER' or request.user.role == 'ADMIN'