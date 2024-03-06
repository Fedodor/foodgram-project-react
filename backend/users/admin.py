from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CustomUser, Subscription
)


@admin.register(CustomUser)
class UserAdmin(UserAdmin):
    pass


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    pass
