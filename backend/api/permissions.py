from rest_framework.permissions import SAFE_METHODS, BasePermission


class AuthorAdminOrReadOnly(BasePermission):
    """Кастомный класс уровней доступа."""
    message = 'Изменение или удаление чужого контента запрещено!'

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (
                obj.author == request.user
                or request.user.is_admin
            )
        )
