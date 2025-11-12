import requests
import json

print('=== TESTING BACKEND API ENDPOINTS ===')

# Test health endpoint
try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    if response.status_code == 200:
        health_data = response.json()
        print('✅ Health endpoint working')
        print(f'   Status: {health_data.get("status")}')
        print(f'   Database: {health_data.get("database")}')
    else:
        print(f'❌ Health endpoint failed: {response.status_code}')
except Exception as e:
    print(f'❌ Health endpoint error: {e}')

# Test products endpoint
try:
    response = requests.get('http://localhost:8000/products', timeout=5)
    if response.status_code == 200:
        products_data = response.json()
        print(f'✅ Products endpoint working - {len(products_data)} products returned')
    else:
        print(f'❌ Products endpoint failed: {response.status_code}')
except Exception as e:
    print(f'❌ Products endpoint error: {e}')

# Test root endpoint
try:
    response = requests.get('http://localhost:8000/', timeout=5)
    if response.status_code == 200:
        root_data = response.json()
        print('✅ Root endpoint working')
        print(f'   Message: {root_data.get("message")}')
    else:
        print(f'❌ Root endpoint failed: {response.status_code}')
except Exception as e:
    print(f'❌ Root endpoint error: {e}')

print('\n=== SUMMARY ===')
print('If all endpoints are failing, the backend server may not be running.')
print('Run: python main.py')
print('Or: uvicorn main:app --reload')
