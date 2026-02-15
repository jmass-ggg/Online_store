# 🛍️ Online Store — Centralized Marketplace (FastAPI + React + PostgreSQL)

A full-stack **online store / marketplace** built to help **local businesses (with or without physical stores)** sell their items in one centralized platform — **for free**.

It works like a **digital shopping center** where multiple sellers can list products and customers can place orders while the system manages:

**Catalog → Cart → Checkout → Multi-Seller Orders → Payments (eSewa / COD)**

---

## ✨ What This Project Does

✅ Centralizes multiple physical/online stores into one marketplace  
✅ Sellers can register and list products with **variants, images, stock**  
✅ Customers can browse, search, add to cart, checkout, and review products  
✅ Multi-seller order fulfillment (each seller handles their own part)  
✅ Payment options: **Cash on Delivery** + **eSewa integration**  
✅ Admin workflow for **seller verification / approval**

---

## 🧠 Core Concepts

### 👥 Roles
- **Customer** → browse, cart, checkout, manage address, orders, reviews
- **Seller** → list products, manage stock/variants, fulfill orders
- **Admin** → approve sellers and manage the platform

### 🏬 Multi-Seller Orders (Marketplace Logic)
When a customer places an order:
- `Order` = main purchase (belongs to the customer)
- `OrderItem` = each line item in the order (includes `seller_id`)
- `OrderFulfillment` = groups items per seller so each seller can accept/hand over their portion

This design makes the marketplace scalable for many sellers.

---

## 🧰 Tech Stack

### Backend
- **FastAPI**
- **SQLAlchemy ORM**
- **JWT Auth** (Access + Refresh Tokens)
- **Role based permissions**
- **PostgreSQL**
- **Docker Compose**
- ✅ **eSewa Payment Integration** (initiate/success/failure/poll)

### Frontend
- **React + Vite**
- Pages: Home, Product listing, Product detail, Checkout, Payment, Login/Register
- Protected routes for authenticated pages

---

## 📂 Project Structure

```text
Online_store/
├─ backend/
│  ├─ api/v1/                 # FastAPI routes
│  ├─ models/                 # SQLAlchemy models
│  ├─ schemas/                # Pydantic schemas
│  ├─ service/                # Business logic layer
│  ├─ utils/                  # JWT + hashing helpers
│  ├─ config/                 # Settings + eSewa utils
│  ├─ uploads/                # Uploaded images
│  ├─ database.py             # DB session/engine
│  └─ main.py                 # FastAPI entry
│
├─ frontend/
│  ├─ public/
│  └─ src/
│     ├─ pages/
│     ├─ routes/
│     ├─ api.js
│     └─ App.jsx
│
├─ docker-compose.yml
├─ .env
└─ README.md
🔥 Main Features
✅ Customer Features
Register/Login (JWT)

Browse categories: Clothes, Accessories, Footwear, Jewelry

Search products

View product details + variants + images

Cart: add/update/remove items

Address management (default shipping/billing)

Place Order / Buy Now

Product reviews

✅ Seller Features
Apply to become a seller

Upload products + variants + images

Manage own products

Accept / handover orders (Seller Management APIs)

✅ Admin Features
Admin authentication

Approve/review sellers

✅ Payment Features
Cash on Delivery

✅ eSewa Payment

initiate payment form

success callback (signature verify + status verify)

failure callback

poll payment status

🧾 Backend API Modules
Located at: backend/api/v1/

login.py → login / refresh / logout

customer.py → register / update / profile

seller.py → seller apply / seller profile

product.py → products + search + variants + images

cart.py → cart operations

order.py → place order / buy now

review.py → product reviews

address.py → customer addresses

seller_management.py → seller order management

esewa_router.py → ✅ eSewa payment routes

Swagger Docs (Docker):

http://localhost:8030/docs

🐳 Run With Docker (Recommended)
This project includes a complete Docker Compose setup with:

PostgreSQL (db)

FastAPI backend

React frontend

1) Create .env in project root
✅ Copy and paste this into .env:

# Database (Docker)
DATABASE_URL=postgresql://postgres:Kanye%4012@db:5432/store

# JWT
SECRET_KEY=secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
Note: %4012 is the URL-encoded form of @12.

2) Start all services
From the root folder (Online_store/):

docker compose up --build
✅ After running:

Frontend → http://localhost:5173

Backend → http://localhost:8030

Swagger API Docs → http://localhost:8030/docs

Postgres exposed at → localhost:5434

3) Stop services
docker compose down
To also delete database data:

docker compose down -v
▶️ Run Locally (Without Docker)
Backend
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
Backend:

http://localhost:8000

Docs:

http://localhost:8000/docs

Frontend
cd frontend
npm install
npm run dev
Frontend:

http://localhost:5173

🧩 ER Diagram (Mermaid)
GitHub supports Mermaid.
If it doesn’t render, use: https://mermaid.live

erDiagram
    ROLES {
        int id PK
        string role_name UK
        string descripted
    }

    ADMIN {
        int id PK
        string username UK
        string email UK
        string hashed_password
        datetime created_at
        datetime updated_at
        string role_name FK
    }

    CUSTOMER {
        int id PK
        string username
        string email UK
        string phone_number
        string hashed_password
        datetime created_at
        datetime updated_at
        string status
        string role_name FK
    }

    SELLER {
        int id PK
        string username
        string email UK
        string phone_number UK
        string hashed_password
        string business_name
        string business_type
        string business_address
        string kyc_document_type
        bigint kyc_document_number
        string bank_account_name
        bigint bank_account_number
        string bank_name
        string bank_branch
        datetime created_at
        datetime updated_at
        string status
        bool is_verified
        string role_name FK
    }

    ADDRESS {
        int id PK
        int customer_id FK
        string full_name
        string phone_number
        string region
        string line1
        string line2
        string postal_code
        string country
        float latitude
        float longitude
        bool is_default_shipping
        bool is_default_billing
        datetime created_at
        datetime updated_at
    }

    PRODUCT {
        int id PK
        string product_name
        string url_slug UK
        string product_category
        string target_audience
        text description
        string image_url
        string status
        int seller_id FK
        datetime created_at
        datetime updated_at
    }

    PRODUCT_VARIANTS {
        int id PK
        int product_id FK
        string sku UK
        string color
        string size
        decimal price
        int stock_quantity
        bool is_active
        datetime created_at
        datetime updated_at
    }

    PRODUCT_IMAGES {
        int id PK
        int product_id FK
        string color
        string image_url
        bool is_primary
        int sort_order
        datetime created_at
    }

    REVIEW {
        int id PK
        int rating
        text comment
        int product_id FK
        int user_id FK
    }

    CARTS {
        int id PK
        int buyer_id FK
        string status
        datetime created_at
        datetime updated_at
    }

    CART_ITEMS {
        int id PK
        int cart_id FK
        int variant_id FK
        int quantity
        decimal price
    }

    ORDERS {
        int id PK
        int buyer_id FK
        string status
        decimal total_price
        string payment_Method
        datetime order_placed
        datetime created_at
        datetime updated_at
    }

    ORDER_ADDRESSES {
        int id PK
        int order_id FK
        string full_name
        string phone_number
        string region
        string line1
        string line2
        string postal_code
        string country
        float latitude
        float longitude
        datetime created_at
    }

    ORDER_ITEMS {
        int id PK
        int order_id FK
        int seller_id FK
        int product_id FK
        int variant_id FK
        int quantity
        decimal unit_price
        decimal line_total
        string item_status
        datetime created_at
        datetime updated_at
    }

    ORDER_FULFILLMENTS {
        int id PK
        int order_id FK
        int seller_id FK
        string fulfillment_status
        decimal seller_subtotal
        datetime accepted_at
        datetime packed_at
        datetime shipped_at
        datetime delivered_at
        datetime created_at
        datetime updated_at
    }

    PAYMENTS {
        int id PK
        int order_id FK
        string provider
        string status
        decimal amount
        string ref_id
        string transaction_uuid UK
        datetime initiated_at
        datetime verified_at
        datetime created_at
        datetime updated_at
    }

    REFRESH_TOKENS {
        int id PK
        string token_hash UK
        string role
        int owner_id
        datetime expires_at
        bool revoked
    }

    ROLES ||--o{ ADMIN : "role_name"
    ROLES ||--o{ CUSTOMER : "role_name"
    ROLES ||--o{ SELLER : "role_name"

    CUSTOMER ||--o{ ADDRESS : has
    CUSTOMER ||--o{ CARTS : has
    CUSTOMER ||--o{ ORDERS : places
    CUSTOMER ||--o{ REVIEW : writes

    SELLER ||--o{ PRODUCT : lists
    SELLER ||--o{ ORDER_ITEMS : receives
    SELLER ||--o{ ORDER_FULFILLMENTS : fulfills

    PRODUCT ||--o{ PRODUCT_VARIANTS : has
    PRODUCT ||--o{ PRODUCT_IMAGES : has
    PRODUCT ||--o{ REVIEW : receives
    PRODUCT ||--o{ ORDER_ITEMS : appears_in

    PRODUCT_VARIANTS ||--o{ CART_ITEMS : in_cart
    PRODUCT_VARIANTS ||--o{ ORDER_ITEMS : purchased_as

    CARTS ||--o{ CART_ITEMS : contains

    ORDERS ||--|| ORDER_ADDRESSES : ships_to
    ORDERS ||--o{ ORDER_ITEMS : contains
    ORDERS ||--o{ ORDER_FULFILLMENTS : grouped_by_seller
    ORDERS ||--o{ PAYMENTS : paid_by
✅ Docker Files & Compose (Copy/Paste Ready)
✅ docker-compose.yml
services:
  db:
    image: postgres:15
    container_name: online_store_db
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: "Kanye@12"
      POSTGRES_DB: store
    ports:
      - "5434:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: online_store_backend
    restart: always
    env_file:
      - .env
    depends_on:
      - db
    ports:
      - "8030:8030"
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8030 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: online_store_frontend
    restart: always
    depends_on:
      - backend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0 --port 5173
    environment:
      - DOCKER=true
      - VITE_API_URL=http://backend:8030
      - VITE_API_BASE_URL=/api

volumes:
  postgres_data:
✅ backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8030

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8030", "--reload"]
✅ frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
✅ eSewa Integration (Backend)
This project includes full eSewa integration in the backend:

GET /payments/esewa/initiate?order_id=... → creates payment attempt and redirects to eSewa form

GET/POST /payments/esewa/success → validates signature + checks eSewa status API and marks payment/order

GET/POST /payments/esewa/failure → returns failure response

GET /payments/esewa/poll/{order_id} → checks current payment status from eSewa status endpoint

File: backend/api/v1/esewa_router.py

