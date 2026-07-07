import json
import urllib.request
import urllib.error
import sys

BASE_URL = 'http://127.0.0.1:8000/api'

def make_request(path, method='GET', headers=None, data=None):
    url = f"{BASE_URL}{path}"
    if headers is None:
        headers = {}
    
    if data is not None:
        req_data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        req_data = None

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode('utf-8')
            return response.status, json.loads(res_data) if res_data else {}
    except urllib.error.HTTPError as e:
        res_data = e.read().decode('utf-8')
        try:
            parsed_err = json.loads(res_data)
        except:
            parsed_err = res_data
        return e.code, parsed_err
    except urllib.error.URLError as e:
        print(f"[FAIL] Could not connect to API at {url}. Make sure your server is running on port 8000.")
        sys.exit(1)

def test_api():
    print("="*60)
    print("         E-COMMERCE REST API INTEGRATION TESTS         ")
    print("="*60)
    
    # 1. Login as Customer
    print("\n[Test 1] Logging in as Customer (user_demo)...")
    login_payload = {'username': 'user_demo', 'password': 'user12345'}
    code, res = make_request('/auth/login/', 'POST', data=login_payload)
    if code != 200:
        print(f"[FAIL] Failed to login: {res}")
        sys.exit(1)
    customer_token = res['access']
    print(f"[OK] Login successful! Token: {customer_token[:20]}...")
    
    customer_headers = {'Authorization': f'Bearer {customer_token}'}

    # 2. Login as Store Manager
    print("\n[Test 2] Logging in as Store Manager (manager_demo)...")
    login_payload = {'username': 'manager_demo', 'password': 'manager12345'}
    code, res = make_request('/auth/login/', 'POST', data=login_payload)
    if code != 200:
        print(f"[FAIL] Failed to login: {res}")
        sys.exit(1)
    manager_token = res['access']
    print(f"[OK] Login successful! Token: {manager_token[:20]}...")
    
    manager_headers = {'Authorization': f'Bearer {manager_token}'}

    # 3. Retrieve Products (Public Access)
    print("\n[Test 3] Fetching products list (Anonymous Access)...")
    code, products = make_request('/products/')
    if code != 200:
        print(f"[FAIL] Failed to fetch products: {products}")
        sys.exit(1)
    print(f"[OK] Successfully fetched {len(products)} products.")
    # Find Galaxy Nexus Z and check its stock
    phone = None
    for p in products:
        if p['name'] == 'Galaxy Nexus Z':
            phone = p
            break
    if not phone:
        print("[FAIL] Could not find product 'Galaxy Nexus Z' in seed data.")
        sys.exit(1)
    initial_stock = phone['stock']
    print(f"[OK] Product 'Galaxy Nexus Z' found. Initial Stock: {initial_stock}, Price: {phone['price']}")

    # 4. Customer Role Permission Validation: Trying to create a product (Should be forbidden)
    print("\n[Test 4] Verifying Customer cannot create products...")
    product_payload = {
        'category': phone['category'],
        'name': 'Unauthorized Product',
        'price': '10.00',
        'stock': 1
    }
    code, res = make_request('/products/', 'POST', headers=customer_headers, data=product_payload)
    if code == 403:
        print("[OK] Correctly received 403 Forbidden.")
    else:
        print(f"[FAIL] Expected 403 Forbidden, got {code}: {res}")
        sys.exit(1)

    # 5. Customer Cart Workflow
    print("\n[Test 5] Customer Cart workflow...")
    # First clear cart
    code, cart_items = make_request('/cart/', 'GET', headers=customer_headers)
    for item in cart_items:
        make_request(f'/cart/{item["id"]}/', 'DELETE', headers=customer_headers)
    print("[OK] Cleared customer cart.")

    # Add 2 items of phone
    cart_payload = {'product': phone['id'], 'quantity': 2}
    code, res = make_request('/cart/', 'POST', headers=customer_headers, data=cart_payload)
    if code != 201:
        print(f"[FAIL] Failed to add product to cart: {res}")
        sys.exit(1)
    cart_item_id = res['id']
    print(f"[OK] Added 2 units of '{phone['name']}' to cart.")

    # Try adding more than stock (e.g. stock + 10)
    excess_payload = {'product': phone['id'], 'quantity': initial_stock + 10}
    code, res = make_request('/cart/', 'POST', headers=customer_headers, data=excess_payload)
    if code == 400:
        print("[OK] Correctly rejected excess quantity with 400 Bad Request.")
    else:
        print(f"[FAIL] Expected 400 Bad Request when exceeding stock, got {code}: {res}")
        sys.exit(1)

    # 6. Order Creation & Stock Deduction
    print("\n[Test 6] Checking out (Creating Order)...")
    code, res = make_request('/orders/', 'POST', headers=customer_headers, data={})
    if code != 201:
        print(f"[FAIL] Order creation failed: {res}")
        sys.exit(1)
    order_id = res['id']
    print(f"[OK] Order #{order_id} created successfully. Total: {res['total_price']}")

    # Verify stock reduction
    code, updated_phone = make_request(f'/products/{phone["id"]}/')
    if code != 200:
        print(f"[FAIL] Failed to retrieve updated product: {updated_phone}")
        sys.exit(1)
    new_stock = updated_phone['stock']
    expected_stock = initial_stock - 2
    if new_stock == expected_stock:
        print(f"[OK] Stock successfully decremented from {initial_stock} to {new_stock}.")
    else:
        print(f"[FAIL] Stock mismatch. Expected {expected_stock}, got {new_stock}.")
        sys.exit(1)

    # Verify cart is now empty
    code, cart_items = make_request('/cart/', 'GET', headers=customer_headers)
    if code == 200 and len(cart_items) == 0:
        print("[OK] Customer cart is now empty.")
    else:
        print(f"[FAIL] Expected empty cart, got: {cart_items}")
        sys.exit(1)

    # 7. Customer trying to change order status (Should be forbidden)
    print("\n[Test 7] Verifying Customer cannot update order status...")
    code, res = make_request(f'/orders/{order_id}/', 'PATCH', headers=customer_headers, data={'status': 'shipped'})
    if code == 403:
        print("[OK] Correctly received 403 Forbidden.")
    else:
        print(f"[FAIL] Expected 403 Forbidden, got {code}: {res}")
        sys.exit(1)

    # 8. Store Manager updating order status
    print("\n[Test 8] Verifying Store Manager can update order status...")
    code, res = make_request(f'/orders/{order_id}/', 'PATCH', headers=manager_headers, data={'status': 'shipped'})
    if code == 200:
        print(f"[OK] Order status successfully updated to '{res['status']}'.")
    else:
        print(f"[FAIL] Failed to update order status: {res}")
        sys.exit(1)

    # 9. Stock restoration on Order Cancellation
    print("\n[Test 9] Verifying Stock Restoration on Order Cancellation...")
    code, res = make_request(f'/orders/{order_id}/', 'PATCH', headers=manager_headers, data={'status': 'canceled'})
    if code != 200:
        print(f"[FAIL] Failed to cancel order: {res}")
        sys.exit(1)
    print("[OK] Order canceled by Manager.")

    code, final_phone = make_request(f'/products/{phone["id"]}/')
    if final_phone['stock'] == initial_stock:
        print(f"[OK] Stock restored back to initial level: {final_phone['stock']}.")
    else:
        print(f"[FAIL] Stock was not restored correctly. Expected {initial_stock}, got {final_phone['stock']}.")
        sys.exit(1)

    print("\n" + "="*60)
    print("     ALL INTEGRATION TESTS PASSED SUCCESSFULLY!     ")
    print("="*60)

if __name__ == '__main__':
    test_api()
