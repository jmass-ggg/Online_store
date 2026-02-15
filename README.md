# 🛍️ Online Store — Centralized Marketplace (FastAPI + React)

A full-stack **online store / marketplace** that helps **local businesses (with or without physical stores)** sell their items in one centralized platform — **for free**.

This project works like a **digital shopping center**:
- Sellers list products (with variants, stock, images)
- Customers browse, add to cart, and checkout
- Orders can contain items from **multiple sellers**
- Payments support **Cash on Delivery** and **eSewa**

---

## 🎯 Why This Project Exists

Many local shops don’t have a strong online presence. This project solves that by providing:
- A single platform for multiple stores/sellers
- A complete e-commerce flow (catalog → cart → checkout → payment)
- A scalable structure for **multi-seller fulfillment**

---

## ✨ Key Features

### 👤 Customer
- Register / Login (JWT)
- Browse categories: **Clothes, Accessories, Footwear, Jewelry**
- Search products
- View product details + variants + images
- Cart management (add / update / remove)
- Manage addresses (default shipping/billing)
- Place orders
- Write product reviews

### 🧑‍💼 Seller
- Seller registration/onboarding
- Upload products + variants (size/color/price/stock)
- Upload multiple product images
- Manage own products
- Handle seller-side fulfillment (accept / hand over / shipped)

### 🛡️ Admin
- Admin authentication
- Seller review / verification workflow

### 💳 Payments
- **Cash on Delivery**
- ✅ **eSewa Integration**
  - Payment initiation (auto-submitted form)
  - Success callback with signature verification
  - Status verification using eSewa status API
  - Failure callback
  - Poll endpoint for frontend status updates

---

## 🧠 Marketplace Order Design (Multi-Seller Support)

This project supports **multi-seller orders** using these tables:

- `Order` → created by a customer
- `OrderItem` → each purchased item (contains `seller_id`)
- `OrderFulfillment` → groups all items **per seller** inside one order
- `OrderAddress` → one shipping address per order
- `Payment` → stores payment attempts and verification results

This makes it easy for each seller to manage only their part of the order.

---

## 🧰 Tech Stack

### Backend
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **JWT Auth** (Access + Refresh tokens)
- **Docker**
- **eSewa Integration**

### Frontend
- **React**
- **Vite**
- Protected routes
- API client in `src/api.js`

---

## 📂 Project Structure

```text
Online_store/
├─ backend/
│  ├─ api/v1/                 # FastAPI routers
│  ├─ models/                 # SQLAlchemy models
│  ├─ schemas/                # Pydantic schemas
│  ├─ service/                # Business logic layer
│  ├─ utils/                  # JWT + hashing helpers
│  ├─ config/                 # Settings + eSewa utils
│  ├─ core/                   # permissions, settings, helpers
│  ├─ uploads/                # Uploaded images
│  ├─ database.py             # DB engine/session
│  └─ main.py                 # FastAPI entry point
│
├─ frontend/
│  ├─ public/                 # Static images
│  └─ src/
│     ├─ pages/               # UI pages (Home, Product, Checkout, Payment)
│     ├─ routes/              # ProtectedRoute
│     ├─ api.js               # API helper
│     └─ App.jsx              # Routes/layout
│
├─ docker-compose.yml
├─ .env
└─ README.md

🚀 Quick Start (Docker — Recommended)
✅ Requirements

Docker + Docker Compose installed

1️⃣ Create .env (in project root)

Create a file named .env in the root folder:

# PostgreSQL inside Docker (IMPORTANT: password must be URL-encoded)
DATABASE_URL=postgresql://postgres:Kanye%4012@db:5432/store

# JWT
SECRET_KEY=secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7


Kanye%4012 is Kanye@12 (because @ must be encoded in URLs).

2️⃣ Start the project

From the root folder (Online_store/):

docker compose up --build

✅ Open the app

Frontend: http://localhost:5173

Backend: http://localhost:8030

Swagger Docs: http://localhost:8030/docs

PostgreSQL exposed: localhost:5434

3️⃣ Stop the project
docker compose down

4️⃣ Stop and delete DB data (reset everything)
docker compose down -v

🧑‍💻 Run Locally (Without Docker)
Backend (FastAPI)
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload


Backend runs at:

http://localhost:8000

Docs: http://localhost:8000/docs

Frontend (React)
cd frontend
npm install
npm run dev


Frontend runs at:

http://localhost:5173

🧾 Docker Configuration
docker-compose.yml (Ports)

Frontend: 5173:5173

Backend: 8030:8030

Postgres: 5434:5432

📚 API Documentation

Swagger UI is available at:

➡️ http://localhost:8030/docs

💳 eSewa Integration (Backend)

The eSewa integration is implemented in:

📍 backend/api/v1/esewa_router.py

✅ Payment Flow

Customer places an order → Order is created

Frontend calls initiate endpoint

Backend creates a Payment record and returns an auto-submit HTML form to eSewa

eSewa redirects to success or failure

On success:

signature is verified

payment status is confirmed via eSewa status API

payment + order status are updated

Frontend can call poll to update payment status

✅ eSewa Endpoints

GET /payments/esewa/initiate?order_id={id}

GET/POST /payments/esewa/success

GET/POST /payments/esewa/failure

GET /payments/esewa/poll/{order_id}

🗄️ Database Overview (Main Tables)

roles, admin, customer, seller

addresses

products, product_variants, product_images

carts, cart_items

orders, order_items, order_fulfillments, order_addresses

payments

reviews

refresh_tokens