from flask import Blueprint, request, jsonify
import werkzeug
import utils.hash as hash_utils
import utils.jwt_handler as jwt_handler
import models
import re
auth_bp = Blueprint("auth", __name__)
db = models.user_repo


@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    
    if not email or not username or not password:
        return jsonify({"error": "Email, username, and password are required"}), 400
    
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Invalid email format"}), 400

    if not re.fullmatch(r"^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$", password):
        return jsonify({"error": "Password must be at least 8 characters long and contain a mix of letters and numbers"}), 400

    existing_email = db.find_user_by_email(email)
    existing_username = db.find_user_by_username(username)
    
    if existing_email or existing_username:
        return jsonify({"error": "Email or Username already exists"}), 400

    genrate_hashed_password = hash_utils.generate_hashed_password(password)  # This should be replaced with actual password hashing logic   

    data_to_save = {
        "email": email,
        "username": username,
        "password": genrate_hashed_password
    }
    db.save(data_to_save)

    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or "").strip()
    username = (data.get('username') or "").strip()
    password = data.get('password')

    if not password or (not email and not username):
        return jsonify({"error": "Provide password and either email or username"}), 400

    user = None
    if email:
        user = db.find_user_by_email(email)
    elif username:
        user = db.find_user_by_username(username)

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not werkzeug.security.check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401
   
    jwt_token = jwt_handler.generate_token(user)

    return jsonify({"message": "Login successful", "token": jwt_token}), 200
