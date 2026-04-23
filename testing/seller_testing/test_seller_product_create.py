import pytest
import requests
import os
BASE_URL = "http://localhost:8000"


def test_create_seller_product():


    login_payload = {
        "email": "user@example.com",
        "password": "stringst"
    }

    login_res = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    assert login_res.status_code == 200

    token = login_res.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }
    IMAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "images")
    images = [
        f for f in os.listdir(IMAGE_DIR)
        if f.endswith(".png")
    ]
    for i in range(20):
        nike_models = [
            "Air Zoom Pegasus",
            "Air Max Plus",
            "Metcon Training Shoe",
            "Revolution Run",
            "Free Run Flyknit",
            "Air Force 1",
            "ZoomX Vaporfly",
            "React Infinity Run","Air Zoom Pegasus",
            "Air Max Plus",
            "Metcon Training Shoe",
            "Revolution Run",
            "Free Run Flyknit",
            "Air Force 1",
            "ZoomX Vaporfly",
            "React Infinity Run",
            "Air Zoom Structure",
            "Downshifter",
            "Winflo",
            "Pegasus Trail",
            "Invincible Run",
            "SuperRep Training",
            "MC Trainer",
            "Renew Ride",
            "Air Monarch",
            "Flex Experience",
            "Journey Run",
            "Streakfly"
        ]

        form_data = {
             "product_name": f"Nike {nike_models[i % len(nike_models)]} {100 + i}",
            "target_audience": "Men",
            "product_category": "Footwear",
            "description": "Comfortable and stylish footwear designed for everyday use. Built with lightweight materials, breathable design, and cushioned sole for all-day comfort. Perfect for casual wear, walking, and daily activities with durable grip and modern style."
        }

        response = requests.post(
            f"{BASE_URL}/product/",
            headers=headers,
            data=form_data
        )

        assert response.status_code == 201

        product_data = response.json()
        product_id = product_data.get("id")

        print(f"\n--- PRODUCT {i+1} ---")
        print("Product ID:", product_id)


        form_variant_data = [
            {"color": "red", "size": "LX", "price": 10000, "stock_quantity": 1000},
            {"color": "red", "size": "L", "price": 1000, "stock_quantity": 1000},
            {"color": "red", "size": "LXX", "price": 1000, "stock_quantity": 1000},
            {"color": "red", "size": "S", "price": 1000, "stock_quantity": 1000},
        ]

        responses = requests.post(
            f"{BASE_URL}/product/{product_id}/variants",
            headers=headers,
            json=form_variant_data   
        )

        print(f"--- VARIANTS {i+1} ---")
        print("Status:", responses.status_code)

        assert responses.status_code == 201
        images_name = images[i % len(images)]

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(BASE_DIR, "..", "images", images_name)
        image_path = os.path.normpath(image_path)

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Missing image: {image_path}")

        with open(image_path, "rb") as f:
            files = [
                ("images", (images_name, f, "image/png"))
            ]

            data = {
                "primary_index": 0
            }

            image_res = requests.post(
                f"{BASE_URL}/product/{product_id}/images",
                headers=headers,
                files=files,
                data=data
            )
        print(f"--- IMAGE {i+1} ---")
        print("Image used:", images_name)
        print("Status:", image_res.status_code)

        assert image_res.status_code == 201
        
        