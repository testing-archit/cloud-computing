import pytest
import os
import tempfile
from datetime import datetime, timedelta
from controller.app import create_app, db
from controller.models import User, Agent, Booking
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create and configure a test app."""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client for the app."""
    return app.test_client()


@pytest.fixture
def admin_token(client):
    """Create an admin user and return JWT token."""
    client.post('/api/auth/register', json={
        'name': 'Admin User',
        'email': 'admin@test.com',
        'password': 'test123456',
        'role': 'admin'
    })
    resp = client.post('/api/auth/login', json={
        'email': 'admin@test.com',
        'password': 'test123456'
    })
    return resp.json['access_token']


@pytest.fixture
def student_token(client):
    """Create a student user and return JWT token."""
    client.post('/api/auth/register', json={
        'name': 'Student User',
        'email': 'student@test.com',
        'password': 'test123456',
        'role': 'student'
    })
    resp = client.post('/api/auth/login', json={
        'email': 'student@test.com',
        'password': 'test123456'
    })
    return resp.json['access_token']


@pytest.fixture
def agent_fixture(app):
    """Create a test agent."""
    with app.app_context():
        agent = Agent(
            name='Test Agent',
            ip='192.168.1.100',
            mac='00:11:22:33:44:55',
            port=5000,
            status='online',
            total_cpu=8,
            available_cpu=8,
            total_mem=16,
            available_mem=16
        )
        db.session.add(agent)
        db.session.commit()
        return agent


class TestAuth:
    """Test authentication endpoints."""
    
    def test_register_success(self, client):
        resp = client.post('/api/auth/register', json={
            'name': 'Test User',
            'email': 'test@test.com',
            'password': 'test123456'
        })
        assert resp.status_code == 201
        assert resp.json['msg'] == 'registered'
    
    def test_register_duplicate_email(self, client):
        client.post('/api/auth/register', json={
            'name': 'User 1',
            'email': 'test@test.com',
            'password': 'test123456'
        })
        resp = client.post('/api/auth/register', json={
            'name': 'User 2',
            'email': 'test@test.com',
            'password': 'test123456'
        })
        assert resp.status_code == 409
        assert 'already registered' in resp.json['error']
    
    def test_login_success(self, client):
        client.post('/api/auth/register', json={
            'name': 'Test',
            'email': 'test@test.com',
            'password': 'test123456'
        })
        resp = client.post('/api/auth/login', json={
            'email': 'test@test.com',
            'password': 'test123456'
        })
        assert resp.status_code == 200
        assert 'access_token' in resp.json
    
    def test_login_invalid_credentials(self, client):
        client.post('/api/auth/register', json={
            'name': 'Test',
            'email': 'test@test.com',
            'password': 'test123456'
        })
        resp = client.post('/api/auth/login', json={
            'email': 'test@test.com',
            'password': 'wrongpassword'
        })
        assert resp.status_code == 401


class TestStudent:
    """Test student endpoints."""
    
    def test_create_booking(self, client, student_token, agent_fixture):
        headers = {'Authorization': f'Bearer {student_token}'}
        start = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        resp = client.post('/api/student/book', json={
            'cpu': 2,
            'memory': '4g',
            'image': 'jupyter/notebook',
            'start_time': start,
            'duration_hr': 2
        }, headers=headers)
        
        assert resp.status_code == 201
        assert 'id' in resp.json
    
    def test_create_booking_past_time(self, client, student_token):
        headers = {'Authorization': f'Bearer {student_token}'}
        start = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        resp = client.post('/api/student/book', json={
            'cpu': 2,
            'memory': '4g',
            'image': 'jupyter/notebook',
            'start_time': start,
            'duration_hr': 2
        }, headers=headers)
        
        assert resp.status_code == 400
        assert 'future' in resp.json['error']
    
    def test_view_bookings(self, client, student_token):
        headers = {'Authorization': f'Bearer {student_token}'}
        resp = client.get('/api/student/bookings', headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json, list)
    
    def test_get_profile(self, client, student_token):
        headers = {'Authorization': f'Bearer {student_token}'}
        resp = client.get('/api/student/profile', headers=headers)
        assert resp.status_code == 200
        assert resp.json['email'] == 'student@test.com'


class TestAdmin:
    """Test admin endpoints."""
    
    def test_list_bookings_admin(self, client, admin_token):
        headers = {'Authorization': f'Bearer {admin_token}'}
        resp = client.get('/api/admin/bookings', headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json, list)
    
    def test_list_bookings_student_forbidden(self, client, student_token):
        headers = {'Authorization': f'Bearer {student_token}'}
        resp = client.get('/api/admin/bookings', headers=headers)
        assert resp.status_code == 403
    
    def test_approve_booking(self, client, admin_token, student_token, agent_fixture, app):
        # Create booking as student
        headers = {'Authorization': f'Bearer {student_token}'}
        start = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        resp = client.post('/api/student/book', json={
            'cpu': 2,
            'memory': '4g',
            'image': 'jupyter/notebook',
            'start_time': start,
            'duration_hr': 2
        }, headers=headers)
        
        booking_id = resp.json['id']
        
        # Approve as admin
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        resp = client.post(f'/api/admin/approve/{booking_id}', json={
            'agent_id': agent_fixture.id
        }, headers=admin_headers)
        
        assert resp.status_code == 200
        assert resp.json['msg'] == 'Booking approved'
    
    def test_reject_booking(self, client, admin_token, student_token, app):
        # Create booking as student
        headers = {'Authorization': f'Bearer {student_token}'}
        start = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        resp = client.post('/api/student/book', json={
            'cpu': 2,
            'memory': '4g',
            'image': 'jupyter/notebook',
            'start_time': start,
            'duration_hr': 2
        }, headers=headers)
        
        booking_id = resp.json['id']
        
        # Reject as admin
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        resp = client.post(f'/api/admin/reject/{booking_id}', json={
            'reason': 'Insufficient resources'
        }, headers=admin_headers)
        
        assert resp.status_code == 200
    
    def test_list_agents(self, client, admin_token, agent_fixture):
        headers = {'Authorization': f'Bearer {admin_token}'}
        resp = client.get('/api/admin/agents', headers=headers)
        assert resp.status_code == 200
        assert len(resp.json) > 0
    
    def test_get_stats(self, client, admin_token):
        headers = {'Authorization': f'Bearer {admin_token}'}
        resp = client.get('/api/admin/stats', headers=headers)
        assert resp.status_code == 200
        assert 'total_bookings' in resp.json


class TestValidation:
    """Test input validation."""
    
    def test_register_missing_fields(self, client):
        resp = client.post('/api/auth/register', json={
            'email': 'test@test.com'
        })
        assert resp.status_code == 400
    
    def test_booking_invalid_cpu(self, client, student_token):
        headers = {'Authorization': f'Bearer {student_token}'}
        start = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        resp = client.post('/api/student/book', json={
            'cpu': 100,  # invalid: > 16
            'memory': '4g',
            'image': 'jupyter/notebook',
            'start_time': start,
            'duration_hr': 2
        }, headers=headers)
        
        assert resp.status_code == 400
