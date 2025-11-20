from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
jwt = JWTManager()
scheduler = BackgroundScheduler()

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///compute.db')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    db.init_app(app)
    jwt.init_app(app)
    migrate = Migrate(app, db)

    from controller.routes.auth import auth_bp
    from controller.routes.student import student_bp
    from controller.routes.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        from controller import models
        db.create_all()
        logger.info("Database initialized")

        # import scheduler here to avoid circular imports (models import controller.app)
        from controller.utils.scheduler import schedule_jobs
    # schedule background jobs
    schedule_jobs(scheduler, app)
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")
    
    logger.info("Flask app created and configured")
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get('DEBUG', 'False') == 'True')
