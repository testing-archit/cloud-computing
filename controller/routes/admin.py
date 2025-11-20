from flask import Blueprint, request, jsonify
from controller.models import db, Booking, Agent, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix="/api/admin")

def admin_required(fn):
    """Decorator to ensure user has admin role."""
    @wraps(fn)
    @jwt_required()
    def decorated(*args, **kwargs):
        identity = get_jwt_identity()
        if identity.get("role") != "admin":
            return jsonify({"error": "Admin role required"}), 403
        return fn(*args, **kwargs)
    return decorated

@admin_bp.get("/bookings")
@admin_required
def list_bookings():
    status = request.args.get("status")
    query = Booking.query
    if status:
        query = query.filter_by(status=status)
    
    bookings = query.order_by(Booking.created_at.desc()).all()
    return jsonify([{
        "id": b.id,
        "user_id": b.user_id,
        "user_name": b.user.name if b.user else "Unknown",
        "agent_id": b.agent_id,
        "status": b.status,
        "start": b.start_time.isoformat() if b.start_time else None,
        "end": b.end_time.isoformat() if b.end_time else None,
        "image": b.image,
        "cpu": b.cpu,
        "memory": b.memory,
        "url": b.access_url,
        "rejection_reason": b.rejection_reason
    } for b in bookings]), 200

@admin_bp.post("/approve/<int:id>")
@admin_required
def approve_booking(id):
    booking = Booking.query.get(id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    if booking.status != "pending":
        return jsonify({"error": f"Cannot approve booking in {booking.status} status"}), 400
    
    # Find best available agent
    data = request.get_json() or {}
    agent_id = data.get("agent_id")
    
    if agent_id:
        agent = Agent.query.get(agent_id)
        if not agent or agent.status != "online":
            return jsonify({"error": "Selected agent not available"}), 400
    else:
        # Auto-select best agent based on resource availability
        agent = Agent.query.filter(
            Agent.status == "online",
            Agent.available_cpu >= booking.cpu,
            Agent.available_mem >= int(booking.memory.rstrip('gm'))
        ).order_by(Agent.available_cpu.desc()).first()
        
        if not agent:
            return jsonify({"error": "No available agents"}), 503
    
    try:
        booking.status = "approved"
        booking.agent_id = agent.id
        db.session.commit()
        logger.info(f"Booking approved: {id} on agent {agent.id}")
        return jsonify({"msg": "Booking approved", "agent_id": agent.id}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Approval failed: {e}")
        return jsonify({"error": "Failed to approve booking"}), 500

@admin_bp.post("/reject/<int:id>")
@admin_required
def reject_booking(id):
    booking = Booking.query.get(id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    if booking.status != "pending":
        return jsonify({"error": f"Cannot reject booking in {booking.status} status"}), 400
    
    data = request.get_json() or {}
    reason = data.get("reason", "Rejected by admin")
    
    try:
        booking.status = "rejected"
        booking.rejection_reason = reason
        db.session.commit()
        logger.info(f"Booking rejected: {id}")
        return jsonify({"msg": "Booking rejected"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Rejection failed: {e}")
        return jsonify({"error": "Failed to reject booking"}), 500

@admin_bp.post("/extend/<int:id>")
@admin_required
def extend_booking(id):
    booking = Booking.query.get(id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    if booking.status != "active":
        return jsonify({"error": "Only active bookings can be extended"}), 400
    
    data = request.get_json() or {}
    hours = data.get("hours", 1)
    
    try:
        booking.end_time = booking.end_time + timedelta(hours=hours)
        db.session.commit()
        logger.info(f"Booking extended: {id} by {hours} hours")
        return jsonify({"msg": "Booking extended", "new_end": booking.end_time.isoformat()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Extend failed: {e}")
        return jsonify({"error": "Failed to extend booking"}), 500

@admin_bp.get("/agents")
@admin_required
def list_agents():
    agents = Agent.query.all()
    return jsonify([{
        "id": a.id,
        "name": a.name,
        "ip": a.ip,
        "status": a.status,
        "available_cpu": a.available_cpu,
        "available_mem": a.available_mem,
        "total_cpu": a.total_cpu,
        "total_mem": a.total_mem,
        "tags": a.tags
    } for a in agents]), 200

@admin_bp.post("/agents/<int:id>/status")
@admin_required
def update_agent_status(id):
    agent = Agent.query.get(id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    data = request.get_json() or {}
    new_status = data.get("status")
    
    if new_status not in ["online", "offline", "maintenance"]:
        return jsonify({"error": "Invalid status"}), 400
    
    try:
        agent.status = new_status
        db.session.commit()
        logger.info(f"Agent status updated: {id} -> {new_status}")
        return jsonify({"msg": "Agent status updated"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Status update failed: {e}")
        return jsonify({"error": "Failed to update agent status"}), 500

@admin_bp.get("/stats")
@admin_required
def get_stats():
    total_bookings = Booking.query.count()
    pending = Booking.query.filter_by(status="pending").count()
    active = Booking.query.filter_by(status="active").count()
    completed = Booking.query.filter_by(status="completed").count()
    online_agents = Agent.query.filter_by(status="online").count()
    
    return jsonify({
        "total_bookings": total_bookings,
        "pending": pending,
        "active": active,
        "completed": completed,
        "online_agents": online_agents
    }), 200
