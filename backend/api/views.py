from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import (
    IsAuthenticated, SAFE_METHODS, IsAuthenticatedOrReadOnly
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
    SubscriptionCreateSerializer,
    RecipePostSerializer, RecipeGetSerializer
)
from core.utils import (
    create_list_of_shopping_cart, create_object, delete_object
)
from recipes.models import (
    Favorite, Ingredient, Recipe, Tag, ShoppingCart, RecipeIngredient
)
from users.models import User, Subscription


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    pagination_class = FoodgramPagination

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        author.save()
        user = request.user
        serializer = SubscriptionCreateSerializer(
            data={
                'user': user.id,
                'author': author.id
            },
            context={'request': request}
        )
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        subscription = get_object_or_404(
            Subscription,
            user=user,
            author=author
        )
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
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        queryset = User.objects.filter(
            subscription__user=self.request.user
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
    permission_classes = IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly
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
            return create_object(request, pk, ShoppingCartSerializer)
        return delete_object(ShoppingCart, request, pk)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return create_object(request, pk, FavoriteSerializer)
        return delete_object(Favorite, request, pk)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_qty=Sum('amount')
        )

        return create_list_of_shopping_cart(ingredients)
