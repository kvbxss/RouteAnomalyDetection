from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    Read permissions are allowed to any authenticated user.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions only for admin users
        return request.user and request.user.is_staff


class IsAuthenticatedOrReadOnlyPublic(permissions.BasePermission):
    """
    Custom permission to allow unauthenticated read access for public endpoints.
    Write permissions require authentication.
    """

    def has_permission(self, request, view):
        # Read permissions allowed for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions require authentication
        return request.user and request.user.is_authenticated


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Admin users have full access
        if request.user and request.user.is_staff:
            return True

        # Check if object has owner field
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # Check if object has created_by field
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False


class CanManageFlightData(permissions.BasePermission):
    """
    Permission for users who can manage flight data uploads and processing.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin users have full access
        if request.user.is_staff:
            return True

        # Check for custom permission (can be added via Django admin)
        return request.user.has_perm('flights.can_manage_flight_data')


class CanRunMLOperations(permissions.BasePermission):
    """
    Permission for users who can run machine learning operations
    like training models and detecting anomalies.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin users have full access
        if request.user.is_staff:
            return True

        # Check for custom permission (can be added via Django admin)
        return request.user.has_perm('flights.can_run_ml_operations')


class ReadOnlyPermission(permissions.BasePermission):
    """
    Permission that only allows read operations (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS and request.user.is_authenticated
