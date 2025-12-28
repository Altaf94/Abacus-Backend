#!/usr/bin/env python3
import urllib.request
import json

def test_registration():
    print("=" * 60)
    print("Testing Registration API")
    print("=" * 60)
    
    url = "http://127.0.0.1:8000/api/auth/register/"
    data = {
        "username": "test_student",
        "email": "student@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "first_name": "Test",
        "last_name": "Student",
        "class_section": "10A",
        "roll_number": "11",
        "role": "student"
    }
    
    req = urllib.request.Request(url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✓ Status: {response.status}")
            print(f"✓ Response:\n{json.dumps(result, indent=2)}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"✗ Error {e.code}:\n{error_body}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_login(username_or_email, password):
    print("\n" + "=" * 60)
    print("Testing Login API")
    print("=" * 60)
    
    url = "http://127.0.0.1:8000/api/auth/login/"
    data = {
        "username": username_or_email,
        "password": password
    }
    
    req = urllib.request.Request(url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✓ Status: {response.status}")
            print(f"✓ Response:\n{json.dumps(result, indent=2)}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"✗ Error {e.code}:\n{error_body}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

if __name__ == "__main__":
    # Test registration
    user = test_registration()
    
    if user:
        # Test login with username
        test_login("test_student", "password123")
        
        # Test login with email
        test_login("student@test.com", "password123")
        
        # Test wrong password
        print("\n" + "=" * 60)
        print("Testing Login with Wrong Password")
        print("=" * 60)
        test_login("test_student", "wrongpassword")
