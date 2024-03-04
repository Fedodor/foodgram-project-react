from rest_framework import serializers


VALIDATE_NAME_ERROR = 'Использовать имя "me" в качестве username запрещено.'


def validate_username(value):
    """Валидация поля юзернейма в сериализаторах и модели."""
    if value == 'me':
        raise serializers.ValidationError(
            VALIDATE_NAME_ERROR
        )
    return value
