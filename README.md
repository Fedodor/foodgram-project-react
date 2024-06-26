# Foodgram

### Описание проекта:
Foodgram — это сайт, где авторизованные пользователи могут подписываться на понравившихся авторов, добавлять рецепты в избранное, в корзину, скачать список ингредиентов в корзине, из добавленных в корзину рецептов.

### Стек технологий:
- Python 3.9.10
- Django 3.2.16
- Django REST framework 3.12.4
- Nginx
- Docker
- Postgres 13.0
- Djoser 2.1.0

### Установка локально:

    1. Клонировать репозиторий и перейти в него в командной строке:

    ```
    git clone git@github.com:Fedodor/kittygram_final.git
    ```

    ```
    cd kittygram_final
    ```

    2. Создайте файл `.env` и заполните его своими данными. Все необходимые переменные перечислены в файле `.env.example`, находящемся в корневой директории проекта.

    3. Создайте и активируйте виртуальное окружение:

    ``` python -m venv venv ```

    ``` source venv/Scripts/activate ```

    4. Установите зависимости проекта:
    
    ``` python -m pip install --upgrade pip ```

    ``` pip install -r requirements.txt ```

    5. Выполните миграции:

    ``` python manage.py migrate ```

    6. Запустите сервер:

    ``` python manage.py runserver ```
  
## Запуск приложения в контейнере на сервере
1. На сервере создайте директорию для приложения:
    ```bash
    mkdir foodgram/infra
    ```
2. В папку _infra_ скопируйте файлы `docker-compose.production.yml`, `nginx.conf`.
3. Там же создайте файл `.env` со следующими переменными:
   ```
   SECRET_KEY=
   ALLOWED_HOSTS=
   ENGINE=django.db.backends.postgresqlpostgresql
   DB_NAME=
   POSTGRES_USER=
   POSTGRES_PASSWORD=
   POSTGRES_DB=
   DB_PORT=5432
   ```
4. В соответствии с `ALLOWED_HOSTS` измените `nginx.conf`.
5. Теперь соберем и запустим контейнер:
   ```bash
   sudo docker compose up --build
   ```
6. В новом окне терминала создадим супер пользователя:
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

## Инфраструктура проекта
**API** - https://localhost/api/ \
**Redoc** - https://localhost/api/docs/ \
**Админка** -https://localhost/admin/

### Примеры нескольких запросов и ответов к API:

1. Получение списка рецептов: \
   **GET** `/api/recipes/` \
   REQUEST
   ```json
   {
     "count": 123,
     "next": "http://127.0.0.1:8000/api/recipes/?page=2",
     "previous": "http://127.0.0.1:8000/api/recipes/?page=1",
     "results": [
       {
         "id": 0,
         "tags": [
           {
             "id": 0,
             "name": "Завтрак",
             "color": "green",
             "slug": "breakfast"
           }
         ],
         "author": {
           "email": "ya@ya.ru",
           "id": 0,
           "username": "user",
           "first_name": "Ivan",
           "last_name": "Zivan",
           "is_subscribed": false
         },
         "ingredients": [
           {
             "id": 0,
             "name": "Курица",
             "measurement_unit": "г",
             "amount": 100
           }
         ],
         "is_favorited": false,
         "is_in_shopping_cart": false,
         "name": "string",
         "image": "https://backend:8080/media/image.jpeg",
         "text": "string",
         "cooking_time": 10
       }
     ]
   }
   ```
2. Регистрация пользователя: \
   **POST** `/api/users/` \
   RESPONSE
   ```json
   {
     "email": "ya@ya.ru",
     "username": "user",
     "first_name": "Ivan",
     "last_name": "Zivan",
     "password": "password"
   }
   ```
   REQUEST
   ```json
   {
   "email": "ya@ya.ru",
   "id": 0,
   "username": "user",
   "first_name": "Ivan",
   "last_name": "Zivan"
   }
   ```
3. Подписаться на пользователя: \
   **POST** `/api/users/{id}/subscribe/`
   REQUEST
   ```json
   {
     "email": "user@example.com",
     "id": 0,
     "username": "user",
     "first_name": "Ivan",
     "last_name": "Zivan",
     "is_subscribed": true,
     "recipes": [
       {
         "id": 0,
         "name": "string",
         "image": "https://backend:8080/media/image.jpeg",
         "cooking_time": 10
       }
     ],
     "recipes_count": 1
   }
   ```

### Автор и проект:

https://foodgramya.ddns.net/

[Fedodor](https://github.com/Fedodor)

(https://github.com/Fedodor/foodgram-project-react/actions/workflows/main.yml/badge.svg)