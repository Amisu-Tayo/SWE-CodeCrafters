from werkzeug.security import generate_password_hash, check_password_hash

# Sample password
password = "testpassword"

# Hash the password using scrypt
password_hash = generate_password_hash(password, method='scrypt')

# Store the hash (simulating storing it in the database)
print("Stored password hash:", password_hash)

# Simulate entering the password for login
entered_password = "testpassword"  # Simulate entering the correct password

# Check if the entered password matches the stored hash
if check_password_hash(password_hash, entered_password):
    print("Password matches.")
else:
    print("Password does not match.")
