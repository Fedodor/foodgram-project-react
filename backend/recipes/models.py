from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.enums import Length
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Тэг',
        max_length=Length.MAX_LEN_RECIPES_CHARFIELD.value,
        unique=True,
    )
    color = ColorField(
        verbose_name='Цвет',
        format='hex',
        unique=True,
        max_length=Length.MAX_LENGHT_COLOR_FIELD.value,
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=Length.MAX_LEN_RECIPES_CHARFIELD.value,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=Length.MAX_LEN_RECIPES_CHARFIELD.value,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=Length.MAX_LEN_MEASUREMENT_UNIT.value,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [models.UniqueConstraint(
            fields=('name', 'measurement_unit'),
            name='unique_ingredient')
        ]


class Recipe(models.Model):

    name = models.CharField(
        verbose_name='Рецепт',
        max_length=Length.MAX_LEN_RECIPES_CHARFIELD.value,
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                Length.MIN_COOKING_TIME.value,
            ),
            MaxValueValidator(
                Length.MAX_COOKING_TIME.value,
            )
        ]
    )
    image = models.ImageField(
        upload_to='rescipes/images/',
        default=None,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список ингредиентов',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Список тегов',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredients_recipe',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredients_recipe',
        on_delete=models.CASCADE,
        default=None,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        default=Length.MIN_AMOUNT_OF_INGREDIENTS.value,
        validators=[
            MinValueValidator(
                Length.MIN_AMOUNT_OF_INGREDIENTS.value,
            ),
            MaxValueValidator(
                Length.MAX_AMOUNT_OF_INGREDIENTS.value,
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Количество ингридиентов'
        ordering = ('recipe',)
        constraints = [models.UniqueConstraint(
            fields=('recipe', 'ingredient'),
            name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return f'{self.amount} {self.ingredient}'


class Favorite(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Избранные рецепты',
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        default=None,
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorite_user',
        default=None,
    )

    class Meta:
        verbose_name = 'Избранные рецепты'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('recipe',)
        constraints = [models.UniqueConstraint(
            fields=('recipe', 'user'),
            name='unique_recipe')
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепты в корзине',
        on_delete=models.CASCADE,
        default=None,
    )
    user = models.ForeignKey(
        User,
        verbose_name='Владелец списка покупок',
        on_delete=models.CASCADE,
        default=None,
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'shopping_cart'
        ordering = ('recipe',)
        constraints = [models.UniqueConstraint(
            fields=('recipe', 'user'),
            name='unique_shopping_cart')
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'
