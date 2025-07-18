# generate_key_file.py
import secrets
import base64

key = base64.urlsafe_b64encode(secrets.token_bytes(32))

with open("secret.key", "wb") as f:
    f.write(key)

print("✅ Key saved to my_secret.key")
print(f"🔑 Key: {key.decode()}")
