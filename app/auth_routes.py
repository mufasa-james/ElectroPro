from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm  # Ensure RegistrationForm is imported

# Define Blueprint
auth = Blueprint('auth', __name__)

# Register Route
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  # Use the correct form name
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(
            Name=form.name.data,
            Email=form.email.data,
            PasswordHash=hashed_password,
            Role='client'  # Default role (since your form does not include role)
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

# Login Route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(Email=form.email.data).first()
        if user and check_password_hash(user.PasswordHash, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

# Logout Route
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
