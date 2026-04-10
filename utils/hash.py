import werkzeug.security

def generate_hashed_password(password):
    return werkzeug.security.generate_password_hash(password)