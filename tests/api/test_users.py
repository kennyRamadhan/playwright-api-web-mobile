"""API tests for /users endpoints."""

import allure
import pytest

from src.api_clients.base_service import APIError
from src.api_clients.user_service import UserService
from src.models.user import UserCreate
from src.utils.data_factory import make_user


@allure.epic("Practice Software Testing")
@allure.feature("Users")
class TestUsers:
    @allure.id("API-USERS-200-001")
    @allure.title("GET /users as admin returns user list")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_admin_lists_users(self, admin_user_service: UserService):
        # Act
        users = await admin_user_service.list_users()

        # Assert
        assert len(users) >= 1
        assert all(u.email for u in users)

    @allure.id("API-USERS-201-001")
    @allure.title("POST /users/register creates a new user")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_register_creates_user(self, public_user_service: UserService):
        # Arrange — demo enforces structured address + strong password
        seed = make_user()
        payload_dict = seed.model_dump(exclude_none=True)
        payload_dict["address"] = {
            "street": seed.address or "1 Test Lane",
            "city": seed.city or "Testville",
            "state": seed.state or "Test State",
            "country": "AU",
            "postcode": seed.postcode or "12345",
        }
        # Drop flat address fields the demo does not accept
        for key in ("city", "state", "country", "postcode"):
            payload_dict.pop(key, None)
        payload_dict["password"] = "StrongPass!2026"

        # Act
        response = await public_user_service._request(
            "POST", "/users/register", json=payload_dict, expected_status=(200, 201)
        )

        # Assert
        body = response.json()
        assert body.get("id")
        assert body.get("email") == seed.email

    @allure.id("API-USERS-200-002")
    @allure.title("GET /users/me returns the current authenticated user")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_get_current_user(self, customer_user_service: UserService, credentials):
        # Act
        user = await customer_user_service.get_current_user()

        # Assert
        assert user.id
        assert user.email == credentials.customer_email

    @allure.id("API-USERS-200-003")
    @allure.title("PUT /users/me updates the current user's profile")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_update_current_user(self, customer_user_service: UserService):
        # Note: PUT /users/me requires the full user payload, not a partial.
        # We fetch current state, mutate phone, and write the whole record back.
        # Arrange
        current_response = await customer_user_service._request("GET", "/users/me")
        current = current_response.json()
        new_phone = "0411223344"
        payload = {
            "first_name": current.get("first_name"),
            "last_name": current.get("last_name"),
            "email": current.get("email"),
            "dob": current.get("dob"),
            "phone": new_phone,
            "address": current.get("address")
            or {
                "street": "1 Test Lane",
                "city": "Testville",
                "country": "AU",
            },
        }

        user_id = current["id"]

        # Act — demo routes profile updates through /users/{id}, not /users/me
        await customer_user_service._request(
            "PUT", f"/users/{user_id}", json=payload, expected_status=(200, 204)
        )

        # Assert
        refreshed = await customer_user_service._request("GET", "/users/me")
        assert refreshed.json().get("phone") == new_phone

    @allure.id("API-USERS-403-001")
    @allure.title("GET /users as non-admin customer returns 403")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_non_admin_cannot_list_users(self, customer_user_service: UserService):
        # Act / Assert
        with pytest.raises(APIError) as exc_info:
            await customer_user_service.list_users()
        assert exc_info.value.status_code == 403


# Re-export so unused-import lint doesn't trip when running file alone
_ = UserCreate
