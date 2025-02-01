from modules.config import generate_api_key

new_user = input("Enter username: ")
new_key = generate_api_key(new_user)
print(f"Generated API key for 'new_user': {new_key}")