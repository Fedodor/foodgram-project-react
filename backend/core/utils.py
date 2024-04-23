from datetime import datetime

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe, RecipeIngredient


RESPONSE_RECIPE_POST_ERROR_MESSAGE = 'Ошибка. Рецепт уже был добавлен.'
RESPONSE_RECIPE_DELETE_ERROR_MESSAGE = 'Ошибка. Рецепт уже был удалён.'


def create_object(request, pk, model_serializer):

    if not Recipe.objects.filter(id=pk).exists():
        return Response(
            {'errors': RESPONSE_RECIPE_DELETE_ERROR_MESSAGE},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = model_serializer(
        data={'recipe': pk},
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(data=serializer.data, status=status.HTTP_201_CREATED)


def delete_object(model, request, pk):
    objects = model.objects.filter(
        user=request.user,
        recipe=get_object_or_404(Recipe, pk=pk),
    )
    objects.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def create_list_of_shopping_cart(user, request):
    today = datetime.today()
    shopping_list = (
        f'Список покупок пользователя: {user.get_full_name()}\n\n'
        f'Дата: {today:%Y-%m-%d}\n\n'
    )
    shopping_list += '\n'.join([
        f'- {ingredient["ingredients__name"]}'
        f'({ingredient["ingredients__measurement_unit"]})'
        f' - {ingredient["cart_amount"]}'
        for ingredient in RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(cart_amount=Sum('amount'))
    ])
    shopping_list += f'\nПосчитано в Foodgram - {today:%Y}'
    return '\n'.join(shopping_list)
