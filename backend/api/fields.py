from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers


class Base64ImageField(Base64ImageField):

    def to_internal_value(self, base64_data):
        if not base64_data:
            raise serializers.ValidationError("This field could not be empty")
        return super().to_internal_value(base64_data)
