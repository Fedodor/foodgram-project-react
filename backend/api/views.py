from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
# from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework import status

from .filters import IngredientFilter, RecipeFilter
from .paginations import CustomPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    CustomUserSerializer, CustomUserCreateSerializer,
    IngredientSerializer, TagSerializer, SubcriptionSerializer,
    SubscriptionCreateSerializer, RecipePostSerializer,
    RecipeGetSerializer
)
from core.utils import create_list_of_shopping_cart, delete, post
from recipes.models import Favorite, Ingredient, Recipe, Tag, ShoppingCart
from users.models import CustomUser, Subscription


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        author = get_object_or_404(
            CustomUser, id=id
        )
        user = request.user
        serializer = SubscriptionCreateSerializer(
            data={'author': author.id},
            context={'request': request})
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save(user=user)
            return Response(SubcriptionSerializer(
                subscription,
                context={'request': request}).data,
                status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            serializer.is_valid(raise_exception=True)
            subscription = Subscription.objects.get(
                user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        # user = request.user
        queryset = Subscription.objects.filter(
            user=request.user).order_by('-id')
        # paginator = PageNumberPagination()
        page = self.paginate_queryset(queryset)
        serializer = SubcriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def paginate_and_serialize(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True,
                context={'request': self.request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True,
            context={'request': self.request})
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        is_subscribed = request.query_params.get('is_subscribed', False)

        if is_subscribed:
            user = request.user
            queryset = CustomUser.objects.prefetch_related(
                'recipes').filter(subscriptions__user=user)
        else:
            queryset = CustomUser.objects.prefetch_related('recipes')

        return self.paginate_and_serialize(queryset)

    @action(detail=False, methods=['POST'])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']

            if self.request.user.check_password(current_password):
                self.request.user.set_password(new_password)
                self.request.user.save()
                return Response(status=204)
            else:
                return Response({'detail': 'Пароли не совпадают.'},
                                status=400)
        else:
            return Response(serializer.errors, status=400)


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
    permission_classes = IsAuthorOrAdminOrReadOnly,
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = self.queryset
        tags = self.request.query_params.getlist('tags', [])
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        author_id = self.request.query_params.get('author', None)
        if author_id is not None:
            queryset = queryset.filter(author_id=author_id)
        if self.request.user.is_anonymous:
            return queryset
        return queryset

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
            return post(ShoppingCart, request.user, pk)
        if request.method == 'DELETE':
            return delete(ShoppingCart, request.user, pk)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return post(Favorite, request.user, pk)
        if request.method == 'DELETE':
            return delete(Favorite, request.user, pk)

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
