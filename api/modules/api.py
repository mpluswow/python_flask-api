from datetime import datetime
from flask import Blueprint, request, jsonify
from modules.db_models import db, Account
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize JWTManager in server.py, but import here for route decorators
jwt = JWTManager()

@api_bp.route('/accounts', methods=['GET'])
@jwt_required()
def get_accounts():
    accounts = Account.query.all()
    accounts_data = [
        {
            'id': a.id,
            'username': a.username,
            'email': a.email,
            'joined': a.joined.strftime('%Y-%m-%d %H:%M:%S') if a.joined else None,
            'last_login': a.last_login.strftime('%Y-%m-%d %H:%M:%S') if a.last_login else None,
            'online': a.online
        } for a in accounts
    ]
    return jsonify(accounts_data), 200

@api_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def api_dashboard():
    current_user = get_jwt_identity()
    return jsonify({
        'message': f"Welcome to your dashboard, {current_user['username']}!"
    }), 200

@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Missing JSON data'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400

    user = Account.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity={'id': user.id, 'username': user.username})
        user.online = True
        user.last_login = datetime.utcnow()
        db.session.commit()
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401

@api_bp.route('/logout', methods=['POST'])
@jwt_required()
def api_logout():
    current_user = get_jwt_identity()
    user = Account.query.get(current_user['id'])
    if user:
        user.online = False
        db.session.commit()
    return jsonify({'message': 'Logged out successfully'}), 200

@api_bp.route('/create-account', methods=['POST'])
def api_create_account():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Missing JSON data'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Username, email, and password are required'}), 400

    # Check if username or email already exists
    if Account.query.filter((Account.username == username) | (Account.email == email)).first():
        return jsonify({'message': 'Username or email already exists'}), 409

    # Create a new account
    hashed_password = generate_password_hash(password)
    new_account = Account(username=username, email=email, password=hashed_password)
    db.session.add(new_account)
    db.session.commit()

    return jsonify({'message': 'Account created successfully'}), 201

