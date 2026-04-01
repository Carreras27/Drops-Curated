import requests
import sys
import json
from datetime import datetime

class HouseOfKitchensAPITester:
    def __init__(self, base_url="https://drops-curated.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.chef_token = None
        self.customer_token = None
        self.chef_user = None
        self.customer_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_menu_items = []
        self.created_order_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_chef_signup(self):
        """Test chef signup"""
        timestamp = datetime.now().strftime('%H%M%S')
        chef_data = {
            "email": f"chef{timestamp}@test.com",
            "password": "password123",
            "name": f"Test Chef {timestamp}",
            "role": "chef",
            "phone": "+1234567890"
        }
        
        success, response = self.run_test(
            "Chef Signup",
            "POST",
            "auth/signup",
            200,
            data=chef_data
        )
        
        if success and 'token' in response:
            self.chef_token = response['token']
            self.chef_user = response['user']
            print(f"   Chef ID: {self.chef_user['id']}")
            return True
        return False

    def test_customer_signup(self):
        """Test customer signup"""
        timestamp = datetime.now().strftime('%H%M%S')
        customer_data = {
            "email": f"customer{timestamp}@test.com",
            "password": "password123",
            "name": f"Test Customer {timestamp}",
            "role": "customer",
            "phone": "+1234567891"
        }
        
        success, response = self.run_test(
            "Customer Signup",
            "POST",
            "auth/signup",
            200,
            data=customer_data
        )
        
        if success and 'token' in response:
            self.customer_token = response['token']
            self.customer_user = response['user']
            print(f"   Customer ID: {self.customer_user['id']}")
            return True
        return False

    def test_auth_me(self):
        """Test auth/me endpoint for both users"""
        # Test chef
        success, _ = self.run_test(
            "Chef Auth Me",
            "GET",
            "auth/me",
            200,
            token=self.chef_token
        )
        
        # Test customer
        success2, _ = self.run_test(
            "Customer Auth Me",
            "GET",
            "auth/me",
            200,
            token=self.customer_token
        )
        
        return success and success2

    def test_create_menu_items(self):
        """Test creating multiple menu items"""
        menu_items = [
            {
                "name": "Margherita Pizza",
                "description": "Classic Italian pizza with fresh mozzarella and basil",
                "price": 18.99,
                "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b",
                "category": "Italian",
                "is_available": True
            },
            {
                "name": "Chicken Biryani",
                "description": "Aromatic basmati rice with spiced chicken",
                "price": 22.50,
                "image_url": "https://images.unsplash.com/photo-1563379091339-03246963d51a",
                "category": "Indian",
                "is_available": True
            },
            {
                "name": "Chocolate Lava Cake",
                "description": "Warm chocolate cake with molten center",
                "price": 8.99,
                "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c",
                "category": "Dessert",
                "is_available": True
            }
        ]
        
        all_success = True
        for item in menu_items:
            success, response = self.run_test(
                f"Create Menu Item: {item['name']}",
                "POST",
                "menu",
                200,
                data=item,
                token=self.chef_token
            )
            if success and 'id' in response:
                self.created_menu_items.append(response)
            else:
                all_success = False
        
        return all_success

    def test_get_menu_items(self):
        """Test getting all menu items"""
        success, response = self.run_test(
            "Get All Menu Items",
            "GET",
            "menu",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} menu items")
            return len(response) >= len(self.created_menu_items)
        return False

    def test_get_chef_menu_items(self):
        """Test getting chef's own menu items"""
        success, response = self.run_test(
            "Get Chef Menu Items",
            "GET",
            "menu/my",
            200,
            token=self.chef_token
        )
        
        if success and isinstance(response, list):
            print(f"   Chef has {len(response)} menu items")
            return len(response) >= len(self.created_menu_items)
        return False

    def test_update_menu_item(self):
        """Test updating a menu item"""
        if not self.created_menu_items:
            return False
            
        item_id = self.created_menu_items[0]['id']
        updated_data = {
            "name": "Updated Margherita Pizza",
            "description": "Updated description",
            "price": 19.99,
            "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b",
            "category": "Italian",
            "is_available": False
        }
        
        success, response = self.run_test(
            "Update Menu Item",
            "PUT",
            f"menu/{item_id}",
            200,
            data=updated_data,
            token=self.chef_token
        )
        
        return success and response.get('name') == 'Updated Margherita Pizza'

    def test_create_order(self):
        """Test creating an order"""
        if not self.created_menu_items:
            return False
            
        order_items = [
            {
                "menu_item_id": self.created_menu_items[0]['id'],
                "name": self.created_menu_items[0]['name'],
                "price": self.created_menu_items[0]['price'],
                "quantity": 2,
                "chef_id": self.created_menu_items[0]['chef_id']
            },
            {
                "menu_item_id": self.created_menu_items[1]['id'],
                "name": self.created_menu_items[1]['name'],
                "price": self.created_menu_items[1]['price'],
                "quantity": 1,
                "chef_id": self.created_menu_items[1]['chef_id']
            }
        ]
        
        order_data = {
            "items": order_items,
            "delivery_address": "123 Test Street, Test City, TC 12345",
            "origin_url": "https://drops-curated.preview.emergentagent.com"
        }
        
        success, response = self.run_test(
            "Create Order",
            "POST",
            "orders",
            200,
            data=order_data,
            token=self.customer_token
        )
        
        if success and 'id' in response:
            self.created_order_id = response['id']
            print(f"   Order ID: {self.created_order_id}")
            print(f"   Total Amount: ${response.get('total_amount', 0)}")
            return True
        return False

    def test_get_orders(self):
        """Test getting orders for both chef and customer"""
        # Customer orders
        success1, response1 = self.run_test(
            "Get Customer Orders",
            "GET",
            "orders/my",
            200,
            token=self.customer_token
        )
        
        # Chef orders
        success2, response2 = self.run_test(
            "Get Chef Orders",
            "GET",
            "orders/my",
            200,
            token=self.chef_token
        )
        
        if success1 and success2:
            print(f"   Customer has {len(response1)} orders")
            print(f"   Chef has {len(response2)} orders")
            return len(response1) > 0 and len(response2) > 0
        return False

    def test_checkout_session(self):
        """Test creating checkout session"""
        if not self.created_order_id:
            return False
            
        checkout_data = {
            "order_id": self.created_order_id,
            "origin_url": "https://drops-curated.preview.emergentagent.com"
        }
        
        success, response = self.run_test(
            "Create Checkout Session",
            "POST",
            "checkout",
            200,
            data=checkout_data,
            token=self.customer_token
        )
        
        if success and 'session_id' in response:
            print(f"   Session ID: {response['session_id']}")
            print(f"   Checkout URL: {response.get('url', 'N/A')}")
            return True
        return False

    def test_chef_earnings(self):
        """Test chef earnings endpoint"""
        success, response = self.run_test(
            "Get Chef Earnings",
            "GET",
            "chef/earnings",
            200,
            token=self.chef_token
        )
        
        if success:
            print(f"   Total Earnings: ${response.get('total_earnings', 0)}")
            print(f"   Total Orders: {response.get('total_orders', 0)}")
            print(f"   Average Rating: {response.get('average_rating', 0)}")
            return True
        return False

    def test_order_status_update(self):
        """Test updating order status"""
        if not self.created_order_id:
            return False
            
        # Test updating order status to confirmed
        success, response = self.run_test(
            "Update Order Status",
            "PUT",
            f"orders/{self.created_order_id}/status?status=confirmed",
            200,
            token=self.chef_token
        )
        
        return success

def main():
    print("🏠 House of Kitchens API Testing")
    print("=" * 50)
    
    tester = HouseOfKitchensAPITester()
    
    # Test sequence
    tests = [
        ("Chef Signup", tester.test_chef_signup),
        ("Customer Signup", tester.test_customer_signup),
        ("Auth Me", tester.test_auth_me),
        ("Create Menu Items", tester.test_create_menu_items),
        ("Get Menu Items", tester.test_get_menu_items),
        ("Get Chef Menu Items", tester.test_get_chef_menu_items),
        ("Update Menu Item", tester.test_update_menu_item),
        ("Create Order", tester.test_create_order),
        ("Get Orders", tester.test_get_orders),
        ("Checkout Session", tester.test_checkout_session),
        ("Chef Earnings", tester.test_chef_earnings),
        ("Order Status Update", tester.test_order_status_update),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print results
    print(f"\n📊 API Test Results")
    print("=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All API tests passed!")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())