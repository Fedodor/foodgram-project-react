from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import (
    IsAuthenticated, SAFE_METHODS
)
from rest_framework.response import Response
from rest_framework.viewsets import (
    ReadOnlyModelViewSet, ModelViewSet
)
from .filters import IngredientFilter, RecipeFilter
from .paginations import FoodgramPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    UserGetSerializer, UserCreatesSerializer,
    FavoriteSerializer, IngredientSerializer,
    TagSerializer, SubcriptionSerializer, ShoppingCartSerializer,
    SubscriptionCreateSerializer, RecipePostSerializer,
    RecipeGetSerializer
)
from core.utils import create_list_of_shopping_cart, delete, post
from recipes.models import Favorite, Ingredient, Recipe, Tag, ShoppingCart
from users.models import User, Subscription


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    pagination_class = FoodgramPagination

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, user_id):
        author = get_object_or_404(
            User, pk=user_id
        )
        author.save()
        user = request.user
        serializer = SubscriptionCreateSerializer(
            data={
                'author': author.id,
                'user': user.id
            },
            context={'request': request})
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        subscription = Subscription.objects.filter(
            user=user, author=author)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreatesSerializer
        return UserGetSerializer

    @action(detail=False, methods=['POST'])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']
        if self.request.user.check_password(current_password):
            self.request.user.set_password(new_password)
            self.request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Пароли не совпадают.'},
                        status=status.HTTP_400_BAD_REQUEST)


class SubscriptionListView(ListAPIView):
    serializer_class = SubcriptionSerializer
    pagination_class = FoodgramPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        current_user = self.request.user
        queryset = User.objects.filter(
            subscription__user=current_user
        )
        return queryset


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.select_related('author')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = IsAuthorOrReadOnly,
    pagination_class = FoodgramPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method not in SAFE_METHODS:
            return RecipePostSerializer
        return RecipeGetSerializer

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return post(request, pk, ShoppingCartSerializer)
        return delete(ShoppingCart, request, pk, ShoppingCartSerializer)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return post(request, pk, FavoriteSerializer)
        return delete(Favorite, request, pk, FavoriteSerializer)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        filename = f'{user.username}_shopping_list.txt'
        shopping_list = create_list_of_shopping_cart(user, request)
        response = HttpResponse(
            shopping_list, content_type="text.txt; charset=utf-8"
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
