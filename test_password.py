import bcrypt

stored_hash = "$2b$12$adTqWgHNFYCk6CfbsSjw1uDSKtNx5rJdVLwm99SrM7br961fiVyFu"

passwords_to_test = ["admin123", "123456", "password"]

for pwd in passwords_to_test:
    if bcrypt.checkpw(pwd.encode('utf-8'), stored_hash.encode('utf-8')):
        print(f"Password '{pwd}' matches the hash")
        break
else:
    print(f"None of the tested passwords match. Hash: {stored_hash}")
    print("Test manual:")
    print(f"admin123: {bcrypt.checkpw('admin123'.encode(), stored_hash.encode())}")
    print(f"123456: {bcrypt.checkpw('123456'.encode(), stored_hash.encode())}")
