# 🛍️ Online Store Frontend

### 💡 Overview  
This is the **frontend** of the full-stack **Online Store** application, built with **React.js** and connected to a **FastAPI backend**.  
It provides users with a modern and responsive interface for exploring products, managing their cart, placing orders, and leaving reviews.

---

## ⚙️ Tech Stack
| Technology | Purpose |
|-------------|----------|
| **React.js** | Component-based UI framework |
| **React Router DOM** | Client-side routing |
| **Axios / Fetch API** | Communication with FastAPI backend |
| **Context API / Redux** | State management |
| **Tailwind CSS / Bootstrap** | Styling and responsive layout |
| **React Icons** | Modern icons for UI |

---

## 🧱 Project Structure
📦 project-root
├── 📁backend
│   ├── main.py
│   ├── database.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── __init__.py
│   │
│   ├── 📁api
│   │   └── 📁v1
│   │       ├── __init__.py
│   │       ├── customer.py
│   │       ├── order.py
│   │       ├── product.py
│       │   ├── review.py
│   │
│   ├── 📁config
│   │   ├── __init__.py
│   │   └── config.py
│   │
│   ├── 📁core
│   │   ├── error_handler.py
│   │   └── permission.py
│   │
│   ├── 📁models
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── customer.py
│   │   ├── order.py
│   │   ├── order_iteam.py
│   │   ├── product.py
│   │   ├── review.py
│   │   └── role.py
│   │
│   ├── 📁schemas
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── order.py
│   │   ├── order_iteam.py
│   │   ├── product.py
│   │   └── review.py
│   │
│   ├── 📁service
│   │   ├── __init__.py
│   │   ├── customer_service.py
│   │   ├── order_service.py
│   │   ├── product_service.py
│   │   └── review_service.py
│   │
│   ├── 📁uploads
│   │   ├── download.jpg
│   │   ├── llll.avif
│   │   └── OIP.webp
│   │
│   └── 📁utils
│       ├── auth.py
│       ├── hashed.py
│       └── jwt.py
│
└── 📁frontend
    ├── 📁public
    │   ├── favicon.ico
    │   ├── index.html
    │   ├── logo192.png
    │   ├── logo512.png
    │   ├── manifest.json
    │   └── robots.txt
    │
    └── 📁src
        ├── App.js
        ├── index.js
        ├── index.css
        │
        ├── 📁api
        │   ├── api.js
        │   └── CartApi.js
        │
        ├── 📁components
        │   ├── Cart.js
        │   ├── Homepage.js
        │   ├── Homepage.module.css
        │   ├── Login.js
        │   ├── OrderConfirmation.js
        │   ├── ProductCard.js
        │   ├── SignUp.js
        │   ├── SignUp.module.css
        │   ├── toast.js
        │   └── validate.js
        │
        ├── 📁img
        │   ├── check.svg
        │   ├── close.svg
        │   ├── email.svg
        │   ├── password.svg
        │   ├── tik.svg
        │   └── user.svg
        │
        └── 📁styles
            └── App.css

---

## 🚀 Key Features
✅ **User Authentication** — Login & register with JWT tokens  
✅ **Product Management** — Browse, filter, and view products  
✅ **Shopping Cart** — Add, remove, and update products  
✅ **Order Management** — Place and track orders  
✅ **Review System** — Add reviews and ratings  
✅ **Responsive Design** — Works on mobile and desktop  

---

## 🧰 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone <repo-url>
cd frontend
2️⃣ Install Dependencies
bash
Copy code
npm install
3️⃣ Start the Development Server
bash
Copy code
npm start
The app will run at:
👉 http://localhost:3000

🔗 Backend Integration
Ensure the FastAPI backend is running (default: http://localhost:8000).

Set the backend base URL in your .env file:

env
Copy code
REACT_APP_API_URL=http://localhost:8000
