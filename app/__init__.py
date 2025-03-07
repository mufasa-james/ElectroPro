from flask import Flask
from config import Config
from app.extensions import db, login_manager
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['REPORT_UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import models after initializing db to avoid circular imports
    from app.models import User, Evaluation, Report, Payment

    # Import and register blueprints
    from app.routes import main as main_blueprint
    from app.auth_routes import auth as auth_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Register CLI commands
    from app.commands import add_admin_command
    app.cli.add_command(add_admin_command)

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
