from controller.app import db
from datetime import datetime
import enum

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="student")  # "admin" or "student"
    department = db.Column(db.String(100), default="General")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    bookings = db.relationship('Booking', backref='user', lazy=True)

class AgentStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(100), nullable=False)
    mac = db.Column(db.String(32))
    port = db.Column(db.Integer, default=5000)
    wol_enabled = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default="offline")  # online/offline/maintenance
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    total_cpu = db.Column(db.Integer, default=4)
    total_mem = db.Column(db.Integer, default=8)  # in GB
    available_cpu = db.Column(db.Integer, default=4)
    available_mem = db.Column(db.Integer, default=8)
    tags = db.Column(db.String(255), default="")  # comma-separated: gpu,ml,heavy
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='agent', lazy=True)

class BookingStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    cpu = db.Column(db.Integer, nullable=False)
    memory = db.Column(db.String(20), nullable=False)  # e.g., "4g"
    image = db.Column(db.String(100), nullable=False)  # docker image
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="pending")
    container_name = db.Column(db.String(100))
    access_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.String(500))
    rejection_reason = db.Column(db.String(500))
