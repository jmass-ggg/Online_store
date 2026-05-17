import pytest
import os
import requests

BASE_URL = "http://localhost:8000"


def test_seller_access():

    # ---------------- LOGIN ---------------- #
    login_payload = {
        "email": "user@example.com",
        "password": "stringst"
    }

    login_res = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_payload,
        timeout=10
    )

    print("LOGIN STATUS:", login_res.status_code)
    print("LOGIN RESPONSE:", login_res.text)

    assert login_res.status_code == 200, login_res.text

    login_data = login_res.json()

    assert "access_token" in login_data, "No access token returned"

    token = login_data["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # ---------------- IMAGE DIRECTORY ---------------- #
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    ACCESSORIES_DIR = os.path.normpath(
        os.path.join(BASE_DIR, "..", "accessories")
    )

    assert os.path.exists(
        ACCESSORIES_DIR
    ), f"Folder not found: {ACCESSORIES_DIR}"

    images = [
        file_name
        for file_name in os.listdir(ACCESSORIES_DIR)
        if file_name.lower().endswith(".png")
    ]

    assert len(images) > 0, "No PNG images found"

    # ---------------- PRODUCT MODELS ---------------- #
    nike_models = [
        "Air Zoom Pegasus",
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

    # ---------------- MAIN LOOP ---------------- #
    for i in range(20):

        # -------- CREATE PRODUCT -------- #
        form_data = {
            "product_name": f"Nike {nike_models[i % len(nike_models)]} {100 + i}",
            "target_audience": "Men",
            "product_category": "Accessories",
            "description": (
                "Comfortable and stylish footwear designed for everyday use. "
                "Built with lightweight materials, breathable design, "
                "and cushioned sole for all-day comfort."
            )
        }

        product_res = requests.post(
            f"{BASE_URL}/product/",
            headers=headers,
            data=form_data,
            timeout=10
        )

        print(f"\n--- PRODUCT {i + 1} ---")
        print("Status:", product_res.status_code)
        print("Response:", product_res.text)

        assert product_res.status_code == 201, product_res.text

        product_data = product_res.json()

        product_id = product_data.get("id")

        assert product_id is not None, "Product ID missing"

        print("Product ID:", product_id)

        # -------- CREATE VARIANTS -------- #
        variant_data = [
            {
                "color": "red",
                "size": "XL",
                "price": 10000,
                "stock_quantity": 1000
            },
            {
                "color": "red",
                "size": "L",
                "price": 1000,
                "stock_quantity": 1000
            },
            {
                "color": "red",
                "size": "XXL",
                "price": 1000,
                "stock_quantity": 1000
            },
            {
                "color": "red",
                "size": "S",
                "price": 1000,
                "stock_quantity": 1000
            }
        ]

        variant_res = requests.post(
            f"{BASE_URL}/product/{product_id}/variants",
            headers=headers,
            json=variant_data,
            timeout=10
        )

        print(f"--- VARIANTS {i + 1} ---")
        print("Status:", variant_res.status_code)
        print("Response:", variant_res.text)

        assert variant_res.status_code == 201, variant_res.text

        # -------- UPLOAD IMAGE -------- #
        image_name = images[i % len(images)]

        image_path = os.path.join(
            ACCESSORIES_DIR,
            image_name
        )

        assert os.path.exists(
            image_path
        ), f"Missing image: {image_path}"

        with open(image_path, "rb") as image_file:

            files = {
                "images": (
                    image_name,
                    image_file,
                    "image/png"
                )
            }

            data = {
                "primary_index": "0"
            }

            image_res = requests.post(
                f"{BASE_URL}/product/{product_id}/images",
                headers=headers,
                files=files,
                data=data,
                timeout=20
            )

        print(f"--- IMAGE {i + 1} ---")
        print("Image used:", image_name)
        print("Status:", image_res.status_code)
        print("Response:", image_res.text)

        assert image_res.status_code == 201, image_res.text