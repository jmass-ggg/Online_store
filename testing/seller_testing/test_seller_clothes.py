import os
import pytest
import requests

BASE_URL = "http://localhost:8000"


def test_create_seller_clothes():
    # 1. Login seller/user
    login_payload = {
        "email": "user@example.com",
        "password": "stringst"
    }

    login_res = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_payload
    )

    print("LOGIN STATUS:", login_res.status_code)
    print("LOGIN RESPONSE:", login_res.text)

    assert login_res.status_code == 200, login_res.text

    token = login_res.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 2. Load images from testing/clothes folder
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CLOTHES_DIR = os.path.join(BASE_DIR, "..", "clothes")
    CLOTHES_DIR = os.path.normpath(CLOTHES_DIR)

    assert os.path.exists(CLOTHES_DIR), f"Clothes folder not found: {CLOTHES_DIR}"

    images = [
        file_name for file_name in os.listdir(CLOTHES_DIR)
        if file_name.lower().endswith(".png")
    ]

    assert len(images) > 0, f"No PNG images found in: {CLOTHES_DIR}"

    clothes_models = [
        "Classic T-Shirt",
        "Slim Fit Jeans",
        "Casual Hoodie",
        "Denim Jacket",
        "Cotton Shirt",
        "Cargo Pants",
        "Polo Shirt",
        "Sweatshirt",
        "Track Pants",
        "Bomber Jacket",
        "Flannel Shirt",
        "Chino Pants",
        "Oversized Tee",
        "Zip Hoodie",
        "Joggers",
        "Wool Sweater",
        "Graphic Tee",
        "Linen Shirt",
        "Puffer Jacket",
        "Relaxed Jeans"
    ]

    # 3. Create 20 clothes products
    for i in range(20):
        form_data = {
            "product_name": f"Nike {clothes_models[i % len(clothes_models)]} {100 + i}",
            "target_audience": "Men",
            "product_category": "Clothes",
            "description": (
                "Comfortable and stylish clothes designed for everyday use. "
                "Built with lightweight materials, breathable design, and modern style."
            )
        }

        product_res = requests.post(
            f"{BASE_URL}/product/",
            headers=headers,
            data=form_data
        )

        print(f"\n--- PRODUCT {i + 1} ---")
        print("Status:", product_res.status_code)
        print("Response:", product_res.text)

        assert product_res.status_code == 201, product_res.text

        product_data = product_res.json()
        product_id = product_data.get("id")

        assert product_id is not None, product_data

        print("Product ID:", product_id)

        # 4. Create product variants
        form_variant_data = [
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
            json=form_variant_data
        )

        print(f"--- VARIANTS {i + 1} ---")
        print("Status:", variant_res.status_code)
        print("Response:", variant_res.text)

        assert variant_res.status_code == 201, variant_res.text

        # 5. Upload clothes image
        image_name = images[i % len(images)]
        image_path = os.path.join(CLOTHES_DIR, image_name)
        image_path = os.path.normpath(image_path)

        assert os.path.exists(image_path), f"Missing image: {image_path}"

        with open(image_path, "rb") as image_file:
            files = [
                ("images", (image_name, image_file, "image/png"))
            ]

            data = {
                "primary_index": "0"
            }

            image_res = requests.post(
                f"{BASE_URL}/product/{product_id}/images",
                headers=headers,
                files=files,
                data=data
            )

        print(f"--- IMAGE {i + 1} ---")
        print("Image used:", image_name)
        print("Status:", image_res.status_code)
        print("Response:", image_res.text)

        assert image_res.status_code == 201, image_res.text