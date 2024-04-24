from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe


RESPONSE_RECIPE_POST_ERROR_MESSAGE = 'Ошибка. Рецепт уже был добавлен.'
RESPONSE_RECIPE_DELETE_ERROR_MESSAGE = 'Ошибка. Рецепт уже был удалён.'
RESPONSE_NOT_AUTHENTICATED_ERROR_MESSAGE = '''
Незарегистрированый пользователь не может удалять рецепты из корзины.'
'''


def create_object(request, pk, model_serializer):

    if not Recipe.objects.filter(id=pk).exists():
        return Response(
            {'errors': RESPONSE_RECIPE_DELETE_ERROR_MESSAGE},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = model_serializer(
        data={
            'recipe': pk,
            'user': request.user.id
        },
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(data=serializer.data, status=status.HTTP_201_CREATED)


def delete_object(model, request, pk):
    user = request.user
    if not user.is_authenticated:
        return Response(
            {'errors': RESPONSE_NOT_AUTHENTICATED_ERROR_MESSAGE},
            status=status.HTTP_400_BAD_REQUEST
        )
    objects = get_object_or_404(
        model,
        user=user,
        recipe=get_object_or_404(Recipe, pk=pk),
    )
    objects.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def create_list_of_shopping_cart(ingredients):
    shopping_list = []
    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        amount = ingredient['ingredient__measurement_unit']
        measurement_unit = ingredient['total_qty']
        shopping_list.append(f'{name}: {amount} {measurement_unit}')
    content = '\n'.join(shopping_list)
    response = FileResponse(content, content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_cart.txt"'
    )
    return response
