from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя."""
    USER = 'user'
    ADMIN = 'admin'
    USER_ROLES = (
        (USER, 'User'),
        (ADMIN, 'Admin')
    )

    role = models.CharField(
        'Роль',
        default=USER,
        choices=USER_ROLES,
        max_length=55,
    )
    email = models.EmailField(
        verbose_name='Почта',
        max_length=254,
        unique=True,
        blank=False,
        null=False
    )

    @property
    def is_user(self):
        return self.role == self.USER

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser