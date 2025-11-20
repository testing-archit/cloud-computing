from flask import Blueprint, request, jsonify
from controller.models import db, Booking, User, Agent
from controller.schemas import BookingRequestSchema, BookingResponseSchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)
student_bp = Blueprint('student', __name__, url_prefix="/api/student")

@student_bp.post("/book")
@jwt_required()
def create_booking():
    identity = get_jwt_identity()
    user_id = identity["id"]
    
    try:
        schema = BookingRequestSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    
    # Validate time
    start = data["start_time"]
    if start < datetime.utcnow():
        return jsonify({"error": "Start time must be in the future"}), 400
    
    end = start + timedelta(hours=int(data["duration_hr"]))
    if (end - start).total_seconds() > 24 * 3600:
        return jsonify({"error": "Booking duration exceeds 24 hours"}), 400
    
    # Check overlapping bookings for same user
    overlap = Booking.query.filter(
        Booking.user_id == user_id,
        Booking.status.in_(["approved", "active"]),
        Booking.start_time < end,
        Booking.end_time > start
    ).first()
    
    if overlap:
        return jsonify({"error": "Booking overlaps with existing session"}), 409
    
    try:
        booking = Booking(
            user_id=user_id,
            cpu=data["cpu"],
            memory=data["memory"],
            image=data["image"],
            start_time=start,
            end_time=end,
            status="pending",
            notes=data.get("tags", "")
        )
        db.session.add(booking)
        db.session.commit()
        logger.info(f"Booking created: {booking.id} by user {user_id}")
        return jsonify({"msg": "Booking submitted", "id": booking.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Booking creation failed: {e}")
        return jsonify({"error": "Failed to create booking"}), 500

@student_bp.get("/bookings")
@jwt_required()
def view_bookings():
    identity = get_jwt_identity()
    user_id = identity["id"]
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    return jsonify([{
        "id": b.id,
        "status": b.status,
        "start": b.start_time.isoformat() if b.start_time else None,
        "end": b.end_time.isoformat() if b.end_time else None,
        "url": b.access_url,
        "image": b.image,
        "cpu": b.cpu,
        "memory": b.memory
    } for b in bookings]), 200

@student_bp.post("/bookings/<int:id>/cancel")
@jwt_required()
def cancel_booking(id):
    identity = get_jwt_identity()
    user_id = identity["id"]
    
    booking = Booking.query.get(id)
    if not booking or booking.user_id != user_id:
        return jsonify({"error": "Booking not found"}), 404
    
    if booking.status not in ["pending", "approved"]:
        return jsonify({"error": f"Cannot cancel booking in {booking.status} status"}), 400
    
    try:
        booking.status = "cancelled"
        db.session.commit()
        logger.info(f"Booking cancelled: {id}")
        return jsonify({"msg": "Booking cancelled"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Cancel failed: {e}")
        return jsonify({"error": "Failed to cancel booking"}), 500

@student_bp.get("/profile")
@jwt_required()
def get_profile():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "department": user.department,
        "active": user.active
    }), 200
