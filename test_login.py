import requests
import json

try:
    response = requests.post('http://localhost:8000/auth/login',
                            json={'username': 'raza123', 'password': '123456'},
                            headers={'Content-Type': 'application/json'})

    print(f'Status Code: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print('✅ Login successful!')
        print(f'User: {data["user"]["username"]}')
        permissions = data["user"]["permissions"]
        print(f'Permissions count: {len(permissions)}')
        print(f'Permissions: {permissions}')
        print(f'Token: {data["access_token"][:50]}...')
    else:
        print(f'Response: {response.json()}')
except Exception as e:
    print(f'Error: {e}')
    print('Note: Server may not be running or accessible')
