from locust import HttpUser, task, between
import random
import string
import time
import uuid


def random_email():
    return f"user_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}@test.com"


def random_username():
    return "user_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class UserRegistrationTest(HttpUser):
    wait_time = between(1, 3)

    @task
    def register_user(self):
        payload = {
            "username": random_username(),
            "email": random_email(),
            "password": "Test@123"
        }

        with self.client.post(
            "/user/register",
            json=payload,
            catch_response=True
        ) as response:

            if response.status_code in (200, 201):
                response.success()
            else:
                response.failure(f"Failed: {response.status_code} | {response.text}")