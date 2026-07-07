# E-commerce REST API
**Student Name:** Francesco Peragine
**Course:** Back-end PPM 2026

## Project Overview
* **Chosen Project Type:** REST API
* **Framework Used:** Django & Django REST Framework (DRF)
* **Database:** SQLite (pre-populated)
* **Live Deployment:** https://progettoppm-wfdb.onrender.com

This application is a RESTful API for an E-commerce platform that implements complete user authentication, role-based access control (RBAC), cart management, stock tracking, and transactional order checkout with stock adjustment logic.

*Note: The deployment runs on Render's free tier, so the instance may spin down after periods of inactivity. The first request after idling can take up to ~50 seconds to respond while it wakes up.*

---

## Implemented Features by User Role
The system supports three user roles: **Customer**, **Store Manager**, and **Admin / Superuser**.

### 1. Customer
* **Authentication:** Can register a new account and log in using JWT token-based authentication.
* **Product Catalog:** Browse products and categories, search products by name/description, and filter products by category.
* **Cart Management:** Add products to the cart, update quantity, and delete items from the cart. Restricts quantities that exceed available product stock.
* **Order Creation:** Checkout the current cart to place an order. This operation is wrapped in a database transaction that validates stock availability, deducts stock, calculates the total price, and clears the cart.

### 2. Store Manager
* **Category Management:** Full CRUD operations on categories (Create, Read, Update, Delete).
* **Product Management:** Full CRUD operations on products (Create, Read, Update, Delete).
* **Order Management:** List and retrieve all orders in the system, and update order statuses (e.g., from 'pending' to 'shipped', 'delivered', or 'canceled').
* **Order Cancellation & Stock Restoration:** If an order status is updated to `canceled`, the system automatically restores the ordered product quantities back to their respective stocks. If a canceled order is set back to pending/shipped, stock is deducted again (with validation checks).

### 3. Admin / Superuser
* **Full Access:** Has all permissions of a Store Manager and Customer, and full access to the Django Admin Panel.

---

## Local Installation & Execution
Follow these steps to run the project locally on your system.

### Prerequisites
* Python 3.10 or higher.

### Steps
1. **Clone or Extract the Repository:**
   Navigate into the project root directory:
   ```bash
   cd ProgettoPPM
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment:**
   * **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   * **Windows (CMD):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   * **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Apply Database Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Seed the Database:**
   Pre-populate the SQLite database with the demo accounts, categories, products, and sample orders:
   ```bash
   python seed_data.py
   ```

7. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   The API will be accessible locally at `http://127.0.0.1:8000/`.

---

## Demo Accounts
The SQLite database contains the following pre-populated demo accounts for immediate testing:

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| `admin_demo` | `admin12345` | Admin / Superuser | Access to Django Admin and all REST endpoints. |
| `manager_demo` | `manager12345` | Store Manager | Access to manage products, categories, and orders. |
| `user_demo` | `user12345` | Customer (Standard) | Access to own cart, browse products, and check out. |

*Note: The SQLite database file is named `db.sqlite3` and is located in the root of the project.*

---

## REST Endpoints Documentation

### 1. Authentication Endpoints

| HTTP Method | URL | Auth Required | Role Allowed | Request Body | Response Example | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/register/` | No | Anonymous | `{"username": "newuser", "password": "securepassword", "email": "new@example.com", "role": "customer"}` | `{"id": 4, "username": "newuser", "email": "new@example.com", "role": "customer"}` | Registers a new user. |
| **POST** | `/api/auth/login/` | No | Anonymous | `{"username": "user_demo", "password": "user12345"}` | `{"refresh": "REF_JWT", "access": "ACC_JWT", "user": {"id": 3, "username": "user_demo", "role": "customer"}}` | Logs in a user, returns JWT tokens and user profile details. |
| **POST** | `/api/auth/token/refresh/` | No | Anonymous | `{"refresh": "REF_JWT"}` | `{"access": "NEW_ACC_JWT"}` | Refreshes an expired access token. |
| **GET** | `/api/auth/profile/` | Yes | Authenticated | *None* | `{"id": 3, "username": "user_demo", "email": "customer@example.com", "role": "customer"}` | Retrieves logged-in user profile. |

### 2. Store Endpoints

| HTTP Method | URL | Auth Required | Role Allowed | Request Body | Response Example | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/categories/` | No | Anonymous | *None* | `[{"id": 1, "name": "Electronics", "slug": "electronics", "description": "Gadgets..."}]` | List all categories. |
| **POST** | `/api/categories/` | Yes | Manager / Admin | `{"name": "Home Decor"}` | `{"id": 4, "name": "Home Decor", "slug": "home-decor", "description": ""}` | Create a new category. |
| **GET** | `/api/products/` | No | Anonymous | *None* | `[{"id": 1, "name": "Smart Phone", "price": "499.00", "stock": 15}]` | List active products. Supports URL filtering `?category=slug` and search `?search=keyword`. |
| **POST** | `/api/products/` | Yes | Manager / Admin | `{"category": 1, "name": "Laptop X", "price": "999.99", "stock": 5}` | `{"id": 5, "name": "Laptop X", "price": "999.99", "stock": 5}` | Create a new product. |
| **DELETE** | `/api/products/<id>/` | Yes | Manager / Admin | *None* | *None* (HTTP 204) | Delete a product. |
| **GET** | `/api/cart/` | Yes | Customer / Admin | *None* | `[{"id": 1, "product": 2, "product_detail": {...}, "quantity": 2, "total_price": "998.00"}]` | Get the customer's current cart items. |
| **POST** | `/api/cart/` | Yes | Customer / Admin | `{"product": 2, "quantity": 1}` | `{"id": 1, "product": 2, "quantity": 1, "total_price": "499.00"}` | Add product to cart (updates quantity if already exists). Validates stock. |
| **PATCH** | `/api/cart/<item_id>/` | Yes | Customer / Admin | `{"quantity": 3}` | `{"id": 1, "product": 2, "quantity": 3, "total_price": "1497.00"}` | Update the quantity of a cart item. Validates stock. |
| **DELETE** | `/api/cart/<item_id>/` | Yes | Customer / Admin | *None* | *None* (HTTP 204) | Remove item from cart. |
| **GET** | `/api/orders/` | Yes | Authenticated | *None* | `[{"id": 1, "status": "pending", "total_price": "998.00", "items": [...]}]` | Customers see their own orders. Managers and Admins see all orders. |
| **POST** | `/api/orders/` | Yes | Customer / Admin | *None* | `{"id": 2, "status": "pending", "total_price": "998.00", "items": [...]}` | Place order from the current cart. Validates stock and decrements it. |
| **PATCH** | `/api/orders/<id>/` | Yes | Manager / Admin | `{"status": "shipped"}` | `{"id": 2, "status": "shipped", "total_price": "998.00"}` | Update order status. If changed to `canceled`, stock is restored. |

---

## Automated Testing

### 1. Django Native Unit Tests
We have implemented 10 comprehensive unit tests covering user auth, permission protection, stock validation, transactional checkout, and cancellation stock recovery.
Run the tests using:
```bash
python manage.py test
```

### 2. Python Integration Script
We have included a complete automated API verification script `test_api.py`. It runs realistic client requests against a running local server, checking permissions, validating stock, creating orders, and verifying response values.
1. Ensure your server is running: `python manage.py runserver`
2. Run the integration tests in a separate terminal:
   ```bash
   python test_api.py
   ```

---

## Manual REST API Testing (HTTPie Workflow)
HTTPie is a command-line HTTP client. Download it at [httpie.io](https://httpie.io/).

Here is a complete testing workflow representing the main actions on both roles.

**Base URL:** All commands below use the local server (`http://127.0.0.1:8000`). To run the same workflow against the deployed instance, simply replace it with `https://progettoppm-wfdb.onrender.com`.

### 1. Authenticating & Token Retrieval
To log in as a Customer and save the access token:
* **Linux/macOS:**
  ```bash
  TOKEN=$(http POST http://127.0.0.1:8000/api/auth/login/ username=user_demo password=user12345 | jq -r '.access')
  ```
* **Windows (PowerShell):**
  ```powershell
  $TOKEN = (http POST http://127.0.0.1:8000/api/auth/login/ username=user_demo password=user12345 | ConvertFrom-Json).access
  ```

*For subsequent commands, substitute `$TOKEN` (PowerShell) or `$TOKEN` (bash/zsh) into the Authorization header.*

---

### 2. Customer Cart Workflow
* **Browse Products (Public):**
  ```bash
  http GET http://127.0.0.1:8000/api/products/
  ```

* **Add Product to Cart:**
  ```bash
  http POST http://127.0.0.1:8000/api/cart/ "Authorization: Bearer $TOKEN" product=2 quantity=2
  ```

* **View Cart:**
  ```bash
  http GET http://127.0.0.1:8000/api/cart/ "Authorization: Bearer $TOKEN"
  ```

* **Place Order (Checkout):**
  ```bash
  http POST http://127.0.0.1:8000/api/orders/ "Authorization: Bearer $TOKEN"
  ```

* **View Own Orders:**
  ```bash
  http GET http://127.0.0.1:8000/api/orders/ "Authorization: Bearer $TOKEN"
  ```

---

### 3. Store Manager Workflow
First, log in as the Store Manager and save their token:
```powershell
$MGR_TOKEN = (http POST http://127.0.0.1:8000/api/auth/login/ username=manager_demo password=manager12345 | ConvertFrom-Json).access
```

* **Create Category:**
  ```bash
  http POST http://127.0.0.1:8000/api/categories/ "Authorization: Bearer $MGR_TOKEN" name="Gaming Accessories" description="Mice, keyboards, controllers"
  ```

* **Create Product:**
  ```bash
  http POST http://127.0.0.1:8000/api/products/ "Authorization: Bearer $MGR_TOKEN" category=1 name="Mechanical Keyboard RGB" price="89.99" stock=12
  ```

* **Update Order Status (e.g., to Shipped):**
  ```bash
  http PATCH http://127.0.0.1:8000/api/orders/1/ "Authorization: Bearer $MGR_TOKEN" status="shipped"
  ```

* **Cancel Order (Triggers Stock Restoration):**
  ```bash
  http PATCH http://127.0.0.1:8000/api/orders/1/ "Authorization: Bearer $MGR_TOKEN" status="canceled"
  ```

---

### 4. Testing Forbidden Action (Access Control Verification)
Verify that a Customer cannot update products:
```bash
http POST http://127.0.0.1:8000/api/products/ "Authorization: Bearer $TOKEN" category=1 name="Hack Item" price="1.00" stock=1
```
*Expected Response: HTTP 403 Forbidden*
