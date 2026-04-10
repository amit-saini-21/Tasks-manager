from flask import Blueprint, jsonify
from utils import jwt_handler

other_bp = Blueprint("other", __name__)


@other_bp.route('/api/alive', methods=['GET'])
def health_check():
    return jsonify({"status": "alive"}), 200


@other_bp.route('/api/user_info', methods=['GET'])
@jwt_handler.token_required
def user_info(current_user):
    return jsonify({
        "email": current_user['email'],
        "username": current_user['username'],
        "id": current_user['id']
    }), 200
