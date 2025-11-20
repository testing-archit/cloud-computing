from flask import Blueprint, request, jsonify
from controller.models import db, User
from controller.schemas import RegisterSchema, LoginSchema
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix="/api/auth")

@auth_bp.post("/register")
def register():
    try:
        schema = RegisterSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409
    
    try:
        user = User(
            name=data["name"],
            email=data["email"],
            password_hash=generate_password_hash(data["password"]),
            role=data.get("role", "student"),
            department="General"  # Always set department to avoid DB errors
        )
        db.session.add(user)
        db.session.commit()
        logger.info(f"User registered: {data['email']}")
        return jsonify({"msg": "registered", "id": user.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@auth_bp.post("/login")
def login():
    try:
        schema = LoginSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    
    user = User.query.filter_by(email=data["email"]).first()
    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    
    if not user.active:
        return jsonify({"error": "Account disabled"}), 403
    
    token = create_access_token(identity={"id": user.id, "role": user.role, "email": user.email})
    logger.info(f"User login: {data['email']}")
    return jsonify({"access_token": token, "role": user.role}), 200

@auth_bp.post("/logout")
def logout():
    return jsonify({"msg": "logged out"}), 200
