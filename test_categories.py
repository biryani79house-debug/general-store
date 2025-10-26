import requests

# Test both environments for the 'General' category

print("=== LOCAL ENVIRONMENT ===")
base_url = 'http://localhost:8000'
login = requests.post(base_url + '/auth/login', json={'username': 'raza123', 'password': '123456'})
if login.status_code == 200:
    token = login.json()['access_token']
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    get_resp = requests.get(base_url + '/categories', headers=headers)
    if get_resp.status_code == 200:
        cats = get_resp.json()
        print(f"Total categories: {len(cats)}")
        print("Last 5 categories:")
        for cat in cats[-5:]:
            print(f"  ID {cat['id']}: {cat['name']}")
        general = any(c['name'] == 'General' for c in cats)
        print(f"General exists locally: {general}")
    else:
        print(f"Failed to get categories: {get_resp.status_code}")
else:
    print("Local login failed")

print()
print("=== PRODUCTION ENVIRONMENT ===")
prod_url = 'https://web-production-9d240.up.railway.app'
prod_login = requests.post(prod_url + '/auth/login', json={'username': 'raza123', 'password': '123456'})
if prod_login.status_code == 200:
    prod_token = prod_login.json()['access_token']
    prod_headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {prod_token}'}
    prod_get = requests.get(prod_url + '/categories', headers=prod_headers)
    if prod_get.status_code == 200:
        prod_cats = prod_get.json()
        print(f"Total categories: {len(prod_cats)}")
        print("Last 5 categories:")
        for cat in prod_cats[-5:]:
            print(f"  ID {cat['id']}: {cat['name']}")
        prod_general = any(c['name'] == 'General' for c in prod_cats)
        print(f"General exists in production: {prod_general}")
    else:
        print(f"Failed to get categories: {prod_get.status_code}")
else:
    print(f"Production login failed: {prod_login.status_code}")
