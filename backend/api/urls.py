from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UsersViewSet, IngredientViewSet,
    TagViewSet, RecipeViewSet,
)

app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register('users', UsersViewSet, basename='users')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
]
