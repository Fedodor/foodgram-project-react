from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User, Subscription
)


@admin.register(User)
class UserAdmin(UserAdmin):
    pass


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    pass
