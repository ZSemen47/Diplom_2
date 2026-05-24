import pytest
import requests
import allure
import uuid
import random

BASE_URL = "https://stellarburgers.education-services.ru/api"

# Генерация уникальных данных
def generate_user_data():
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"user_{unique_id}@test.com",
        "password": "password123",
        "name": f"User_{unique_id}"
    }

# Получение списка ингредиентов
def get_ingredient_ids():
    """Возвращает два случайных ID ингредиентов из ответа API"""
    response = requests.get(f"{BASE_URL}/ingredients")
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data"):
            # Получаем список всех ингредиентов
            ingredients = data["data"]
            # Выбираем два случайных ингредиента
            random_ingredients = random.sample(ingredients, 2)
            # Возвращаем их ID
            return [ing["_id"] for ing in random_ingredients]
    # Если что-то пошло не так - используем запасные ID
    return ["61c0c5a71d1f82001bdaaa6d", "61c0c5a71d1f82001bdaaa6f"]

@allure.epic("Stellar Burgers API")
class TestCreateUser:
    @allure.title("Создание уникального пользователя")
    def test_create_unique_user(self):
        user_data = generate_user_data()
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        assert response.status_code == 200

    @allure.title("Создание пользователя, который уже зарегистрирован")
    def test_create_existing_user(self):
        user_data = generate_user_data()
        # Первая регистрация
        requests.post(f"{BASE_URL}/auth/register", json=user_data)
        # Повторная регистрация
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        assert response.status_code == 403

    @allure.title("Создание пользователя без одного из обязательных полей")
    @pytest.mark.parametrize("missing_field", ["email", "password", "name"])
    def test_create_user_missing_field(self, missing_field):
        user_data = generate_user_data()
        del user_data[missing_field]
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        assert response.status_code == 403


@allure.epic("Stellar Burgers API")
class TestLoginUser:
    @allure.title("Логин под существующим пользователем")
    def test_login_existing_user(self):
        user_data = generate_user_data()
        requests.post(f"{BASE_URL}/auth/register", json=user_data)
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200

    @allure.title("Логин с неверным логином и паролем")
    def test_login_invalid_credentials(self):
        login_data = {"email": "wrong@test.com", "password": "wrongpass"}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 401


@allure.epic("Stellar Burgers API")
class TestUpdateUser:
    @allure.title("Изменение данных пользователя с авторизацией")
    def test_update_user_authorized(self):
        user_data = generate_user_data()
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        access_token = reg_resp.json()["accessToken"]
        new_data = {"name": "NewName"}
        headers = {"Authorization": access_token}
        response = requests.patch(f"{BASE_URL}/auth/user", json=new_data, headers=headers)
        assert response.status_code == 200

    @allure.title("Изменение данных пользователя без авторизации")
    def test_update_user_unauthorized(self):
        new_data = {"name": "NewName"}
        response = requests.patch(f"{BASE_URL}/auth/user", json=new_data)
        assert response.status_code == 401


@allure.epic("Stellar Burgers API")
class TestCreateOrder:
    @allure.title("Создание заказа с авторизацией")
    def test_create_order_authorized(self):
        user_data = generate_user_data()
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        access_token = reg_resp.json()["accessToken"]
        ingredients = get_ingredient_ids()
        order_data = {"ingredients": ingredients}
        headers = {"Authorization": access_token}
        response = requests.post(f"{BASE_URL}/orders", json=order_data, headers=headers)
        assert response.status_code == 200

    @allure.title("Создание заказа без авторизации")
    def test_create_order_unauthorized(self):
        ingredients = get_ingredient_ids()
        order_data = {"ingredients": ingredients}
        response = requests.post(f"{BASE_URL}/orders", json=order_data)
        assert response.status_code == 200

    @allure.title("Создание заказа с ингредиентами")
    def test_create_order_with_ingredients(self):
        user_data = generate_user_data()
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        access_token = reg_resp.json()["accessToken"]
        ingredients = get_ingredient_ids()
        order_data = {"ingredients": ingredients}
        headers = {"Authorization": access_token}
        response = requests.post(f"{BASE_URL}/orders", json=order_data, headers=headers)
        assert response.status_code == 200

    @allure.title("Создание заказа без ингредиентов")
    def test_create_order_no_ingredients(self):
        user_data = generate_user_data()
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        access_token = reg_resp.json()["accessToken"]
        order_data = {"ingredients": []}
        headers = {"Authorization": access_token}
        response = requests.post(f"{BASE_URL}/orders", json=order_data, headers=headers)
        assert response.status_code == 400

    @allure.title("Создание заказа с неверным хешем ингредиентов")
    def test_create_order_invalid_ingredient_hash(self):
        user_data = generate_user_data()
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        access_token = reg_resp.json()["accessToken"]
        order_data = {"ingredients": ["invalid_hash_123"]}
        headers = {"Authorization": access_token}
        response = requests.post(f"{BASE_URL}/orders", json=order_data, headers=headers)
        assert response.status_code == 500


@allure.epic("Stellar Burgers API")
class TestGetUserOrders:
    @allure.title("Получение заказов авторизованного пользователя")
    def test_get_orders_authorized(self):
        user_data = generate_user_data()
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        access_token = reg_resp.json()["accessToken"]
        # Создадим заказ
        ingredients = get_ingredient_ids()
        order_data = {"ingredients": ingredients}
        headers = {"Authorization": access_token}
        requests.post(f"{BASE_URL}/orders", json=order_data, headers=headers)
        # Получаем заказы пользователя
        response = requests.get(f"{BASE_URL}/orders", headers=headers)
        assert response.status_code == 200


    @allure.title("Получение заказов неавторизованного пользователя")
    def test_get_orders_unauthorized(self):
        response = requests.get(f"{BASE_URL}/orders")
        assert response.status_code == 401