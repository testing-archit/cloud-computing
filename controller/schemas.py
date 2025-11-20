from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timedelta

class RegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(validate=validate.OneOf(["admin", "student"]), load_default="student")

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class BookingRequestSchema(Schema):
    cpu = fields.Int(required=True, validate=validate.Range(min=1, max=16))
    memory = fields.Str(required=True, validate=validate.Regexp(r'^\d+[gm]$'))
    image = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    start_time = fields.DateTime(required=True)
    duration_hr = fields.Int(required=True, validate=validate.Range(min=1, max=24))
    tags = fields.Str(load_default="")  # optional: filter agents by tags

class ApproveBookingSchema(Schema):
    agent_id = fields.Int(required=True)

class BookingResponseSchema(Schema):
    id = fields.Int()
    status = fields.Str()
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    access_url = fields.Str(allow_none=True)
    image = fields.Str()
    cpu = fields.Int()
    memory = fields.Str()

class AgentSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    ip = fields.Str()
    status = fields.Str()
    available_cpu = fields.Int()
    available_mem = fields.Int()
    total_cpu = fields.Int()
    total_mem = fields.Int()
