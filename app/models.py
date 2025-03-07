from app.extensions import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'Users'

    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(255), nullable=False)
    Email = db.Column(db.String(255), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    Role = db.Column(db.Enum('Client', 'Evaluator', 'Admin'), nullable=False)
    CreatedAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    evaluations_client = db.relationship('Evaluation', foreign_keys='Evaluation.ClientID', backref='client', lazy=True)
    evaluations_evaluator = db.relationship('Evaluation', foreign_keys='Evaluation.EvaluatorID', backref='evaluator', lazy=True)
    payments = db.relationship('Payment', backref='client', lazy=True)

    # Explicitly define get_id()
    def get_id(self):
        return str(self.UserID)  # Flask-Login expects a string


# Update the Evaluation class to include the evaluation_form relationship
class Evaluation(db.Model):
    __tablename__ = 'Evaluations'

    EvaluationID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ClientID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    EvaluatorID = db.Column(db.Integer, db.ForeignKey('Users.UserID', ondelete='SET NULL'), nullable=True)
    Status = db.Column(db.Enum('Pending', 'In Progress', 'Completed'), server_default="Pending")
    Score = db.Column(db.Numeric(5, 2), nullable=True)
    Comments = db.Column(db.Text, nullable=True)
    CreatedAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    report = db.relationship('Report', backref='evaluation', uselist=False, lazy=True)
    evaluation_form = db.relationship('EvaluationForm', backref='evaluation', uselist=False, lazy=True)


# Add this new EvaluationForm class
class EvaluationForm(db.Model):
    __tablename__ = 'EvaluationForms'

    FormID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EvaluationID = db.Column(db.Integer, db.ForeignKey('Evaluations.EvaluationID', ondelete='CASCADE'), unique=True)
    Location = db.Column(db.String(255), nullable=False)
    EvaluationDate = db.Column(db.Date, nullable=False)

    # Section 1: General Compliance
    contractor_license = db.Column(db.Boolean, nullable=False)
    contractor_license_remarks = db.Column(db.Text)
    design_compliance = db.Column(db.Boolean, nullable=False)
    design_compliance_remarks = db.Column(db.Text)
    documentation = db.Column(db.Boolean, nullable=False)
    documentation_remarks = db.Column(db.Text)
    testing_records = db.Column(db.Boolean, nullable=False)
    testing_records_remarks = db.Column(db.Text)
    wiring_regulations = db.Column(db.Boolean, nullable=False)
    wiring_regulations_remarks = db.Column(db.Text)

    # Section 2: Electrical System Safety
    circuit_breakers = db.Column(db.Boolean, nullable=False)
    circuit_breakers_remarks = db.Column(db.Text)
    earthing_bonding = db.Column(db.Boolean, nullable=False)
    earthing_bonding_remarks = db.Column(db.Text)
    exposed_wires = db.Column(db.Boolean, nullable=False)
    exposed_wires_remarks = db.Column(db.Text)
    rcd_installed = db.Column(db.Boolean, nullable=False)
    rcd_installed_remarks = db.Column(db.Text)
    panel_labeling = db.Column(db.Boolean, nullable=False)
    panel_labeling_remarks = db.Column(db.Text)

    # Section 3: Workplace Safety & Equipment Compliance
    equipment_inspection = db.Column(db.Boolean, nullable=False)
    equipment_inspection_remarks = db.Column(db.Text)
    safety_signage = db.Column(db.Boolean, nullable=False)
    safety_signage_remarks = db.Column(db.Text)
    emergency_switches = db.Column(db.Boolean, nullable=False)
    emergency_switches_remarks = db.Column(db.Text)
    circuit_loading = db.Column(db.Boolean, nullable=False)
    circuit_loading_remarks = db.Column(db.Text)
    safety_procedures = db.Column(db.Boolean, nullable=False)
    safety_procedures_remarks = db.Column(db.Text)

    # Section 4: Final Assessment
    overall_rating = db.Column(db.Enum('Excellent', 'Satisfactory', 'Needs Improvement', 'Non-Compliant'),
                               nullable=False)
    corrective_actions = db.Column(db.Text)
    additional_comments = db.Column(db.Text)
    evaluator_signature = db.Column(db.String(255), nullable=False)
    signed_date = db.Column(db.Date, nullable=False)

    CreatedAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                          onupdate=db.func.current_timestamp())

# Report Model
class Report(db.Model):
    __tablename__ = 'Reports'

    ReportID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EvaluationID = db.Column(db.Integer, db.ForeignKey('Evaluations.EvaluationID', ondelete='CASCADE'), unique=True)
    ReportFilePath = db.Column(db.String(255), nullable=False)
    GeneratedAt = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

# Payment Model
class Payment(db.Model):
    __tablename__ = 'Payments'

    PaymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ClientID = db.Column(db.Integer, db.ForeignKey('Users.UserID'), nullable=False)
    Amount = db.Column(db.Numeric(10, 2), nullable=False)
    Status = db.Column(db.Enum('Pending', 'Completed', 'Failed'), server_default="Pending")
    PaidAt = db.Column(db.TIMESTAMP, nullable=True)

class IssueReport(db.Model):
    __tablename__ = 'issue_reports'
    
    ReportID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(255), nullable=False)
    IssueType = db.Column(db.String(50), nullable=False)
    Description = db.Column(db.Text, nullable=False)
    StepsToReproduce = db.Column(db.Text)
    Status = db.Column(db.String(20), default='New')  # New, In Progress, Resolved, Closed
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    UpdatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    Resolution = db.Column(db.Text)
    ResolvedAt = db.Column(db.DateTime)
