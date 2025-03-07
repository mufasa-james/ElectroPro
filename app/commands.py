import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

@click.command('add-admin')
@click.argument('email')
@click.argument('password')
@with_appcontext
def add_admin_command(email, password):
    """Add an admin user to the database."""
    # Check if user already exists
    if User.query.filter_by(Email=email).first():
        click.echo('Error: User with this email already exists.')
        return

    # Create new admin user
    admin = User(
        Name='Admin',
        Email=email,
        PasswordHash=generate_password_hash(password),
        Role='Admin'
    )
    
    try:
        db.session.add(admin)
        db.session.commit()
        click.echo(f'Successfully created admin user with email: {email}')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating admin user: {str(e)}') 