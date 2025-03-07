import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mysecretkey')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://electropro_user:ElectroProPass123!@localhost/electropro_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REPORT_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'reports')
    
    # Create reports directory if it doesn't exist
    os.makedirs(REPORT_UPLOAD_FOLDER, exist_ok=True)
