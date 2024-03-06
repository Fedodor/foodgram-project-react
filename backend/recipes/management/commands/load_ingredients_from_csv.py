import csv

from django.core.management import BaseCommand
from tqdm import tqdm

from recipes.models import (
    Ingredient
)


class Command(BaseCommand):

    def handle(self, *args, **options):

        with open(
            'recipes/data/ingredients.csv', 'r', encoding='utf-8'
        ) as csvfile:
            reader = csv.reader(csvfile)
            for row in tqdm(reader):
                Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1]
                )
