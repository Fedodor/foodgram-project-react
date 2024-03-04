import base64

from django.core.files.base import ContentFile
from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import exceptions, serializers
from rest_framework.validators import UniqueValidator

from core.enums import Length
from recipes.models import (
    Ingredient, Tag, Recipe, RecipeIngredient
)
from users.models import CustomUser, Subscription


SUBSCRIPTION_NOT_FOUND_ERROR = 'Подписка не найдена'
RE_SUBSCRIPTION_VALIDATION_ERROR = 'Нельзя подписаться ещё раз'
ME_SUBSCRIPTION_VALIDATION_ERROR = 'Нельзя подписаться на самого себя'
RECIPE_VALIDATION_ERROR = 'Рецепт уже в корзине.'
INGREDIENTS_NOT_FOUND_ERROR = 'Количество ингредиентов не должно быть равно 0.'
RECIPE_NOT_FOUND_VALIDATION_ERROR = 'Рецепт не найден в корзине.'
RECIPE_VALIDATION_ERROR_FAVORITES = 'Рецепт уже добавлен в избранное.'
NOT_FOUND_FIELDS_ERROR = 'Не хватает поля тэгов или ингредиентов.'


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )
        read_only_fields = ('id', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all())])

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'password', 'username', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',


class RecipeMiniSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = '__all__',


class SubcriptionSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )
        read_only_fields = 'all',

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Subscription.objects.filter(
            user=user,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        queryset = Recipe.objects.filter(author=obj.author)
        if request and not request.user.is_anonymous:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    queryset = queryset[:int(recipes_limit)]
                except TypeError:
                    pass
        return RecipeMiniSerializer(
            queryset, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']
        if self.context['request'].method == 'POST':
            if user == author:
                raise exceptions.ValidationError(
                    ME_SUBSCRIPTION_VALIDATION_ERROR
                )
            if Subscription.objects.filter(
                user=user, author=author
            ).exists():
                raise exceptions.ValidationError(
                    RE_SUBSCRIPTION_VALIDATION_ERROR
                )
        elif self.context['request'].method == 'DELETE':
            try:
                Subscription.objects.get(user=user, author=author)
            except Subscription.DoesNotExist:
                raise serializers.ValidationError(
                    SUBSCRIPTION_NOT_FOUND_ERROR
                )
        return data

    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)


class RecipeIngredientPostSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField(
        write_only=True,
        min_value=Length.MIN_AMOUNT_OF_INGREDIENTS.value,
        max_value=Length.MAX_AMOUNT_OF_INGREDIENTS.value
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, amount):
        if amount < 1:
            raise exceptions.ValidationError(
                {
                    'ingredients': INGREDIENTS_NOT_FOUND_ERROR
                }
            )
        return amount

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'id': data['id'],
            'name': data['name'],
            'measurement_unit': data['measurement_unit'],
            'amount': data['amount']
        }

    def to_internal_value(self, data):
        if isinstance(data, dict):
            ingredient_id = data.get('id')
            amount = data.get('amount')
            if ingredient_id is not None:
                return {'id': ingredient_id, 'amount': amount}
        return super().to_internal_value(data)


class RecipeGetSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, recipe):
        ingredients = recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F(
                'ingredients_recipe__amount'
            )
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and user.favorites_user.filter(
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and user.shopping_cart.filter(
            recipe=obj
        ).exists()


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientPostSerializer(
        many=True, required=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(
        min_value=Length.MIN_COOKING_TIME.value,
        max_value=Length.MAX_COOKING_TIME.value
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'text', 'cooking_time', 'image',
        )
        required_fields = ('tags', 'ingredients')

    def validate(self, data):
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')
        if not tags or not ingredients:
            raise exceptions.ValidationError(
                NOT_FOUND_FIELDS_ERROR
            )
        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise exceptions.ValidationError(
                {'ingredients': 'Должен быть хотя бы один ингредиент.'}
            )
        set_of_ingredients = set()
        for item in ingredients:
            if not Ingredient.objects.filter(id=item['id']).exists():
                raise serializers.ValidationError(
                    'Указанного Ингредиента не существует')
            ingredient = get_object_or_404(
                Ingredient.objects.all(), id=item['id']
            )
            if ingredient in set_of_ingredients:
                raise exceptions.ValidationError(
                    {'ingredients': 'Ингредиенты не могут повторяться.'}
                )
            set_of_ingredients.add(ingredient)
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise exceptions.ValidationError(
                {'tags': 'Должен быть хотя бы один тег.'}
            )
        set_of_tags = set()
        for tag in tags:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Указанного тега не существует')
            if tag in set_of_tags:
                raise exceptions.ValidationError(
                    {'tags': 'Теги не могут повторяться.'}
                )
            set_of_tags.add(tag)
        return tags

    def create_ingredients_amounts(self, ingredients_data, recipe):
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            ingredient = Ingredient.objects.get(id=ingredient_id)
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredients=ingredient,
                    amount=ingredient_data['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        _ = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        instance = super().create(validated_data)
        instance.tags.set(tags)
        self.create_ingredients_amounts(
            recipe=instance, ingredients_data=ingredients_data
        )
        return instance

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.image.delete()
        instance.image = validated_data.get('image', instance.image)
        tags_data = validated_data.pop('tags', [])
        instance.tags.set(tags_data)
        ingredients_data = validated_data.pop('ingredients', [])
        recipe_ingredients = instance.ingredients_recipe.all()
        recipe_ingredients.delete()
        self.create_ingredients_amounts(
            recipe=instance, ingredients_data=ingredients_data
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGetSerializer(instance, context=context).data
