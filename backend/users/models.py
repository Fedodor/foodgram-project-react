from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models

from api.validators import validate_username
from core.enums import Length


class User(AbstractUser):
    """Модель пользователя."""

    ADMIN = 'admin'
    USER = 'user'
    USER_ROLES = [
        (USER, 'Аутентифицированный пользователь'),
        (ADMIN, 'Администратор'),
    ]
    username = models.CharField(
        verbose_name='Псевдоним',
        default='username',
        max_length=Length.MAX_LENGTH_USERNAME.value,
        unique=True,
        validators=(
            [
                RegexValidator(regex=r'^[\w.@+-]+\Z'),
                UnicodeUsernameValidator(),
                validate_username
            ]
        )
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=Length.MAX_LENGTH_PASSWORD.value,
    )
    email = models.EmailField(
        'Почта',
        unique=True,
        default='some@example.com',
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=Length.MAX_LENGTH_FIRST_NAME.value,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=Length.MAX_LENGTH_LAST_NAME.value,
    )
    role = models.CharField(
        verbose_name='Права доступа',
        max_length=Length.MAX_LENGTH_ROLE.value,
        choices=USER_ROLES,
        default=USER
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name'
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def is_user(self):
        return self.role == self.USER

    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    def __str__(self):
        return self.username


class Subscription(models.Model):

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='subscriber',
        on_delete=models.CASCADE,
        default=None,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='subscription',
        on_delete=models.CASCADE,
        default=None,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = [models.UniqueConstraint(
            fields=('user', 'author'),
            name='unique_subscriber')
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
