from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateField, RadioField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
import re

def validate_password_strength(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('Password must contain at least one special character')

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=255)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[('Client', 'Client'), ('Evaluator', 'Evaluator')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

# Add LoginForm (It was missing)
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class EvaluationBookingForm(FlaskForm):
    property_type = SelectField('Property Type', choices=[
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial')
    ])
    street_address = StringField('Street Address', validators=[DataRequired()])
    town = StringField('Town/City', validators=[DataRequired()])
    county = SelectField('County', choices=[
        ('Baringo', 'Baringo'),
        ('Bomet', 'Bomet'),
        ('Bungoma', 'Bungoma'),
        ('Busia', 'Busia'),
        ('Elgeyo/Marakwet', 'Elgeyo/Marakwet'),
        ('Embu', 'Embu'),
        ('Garissa', 'Garissa'),
        ('Homa Bay', 'Homa Bay'),
        ('Isiolo', 'Isiolo'),
        ('Kajiado', 'Kajiado'),
        ('Kakamega', 'Kakamega'),
        ('Kericho', 'Kericho'),
        ('Kiambu', 'Kiambu'),
        ('Kilifi', 'Kilifi'),
        ('Kirinyaga', 'Kirinyaga'),
        ('Kisii', 'Kisii'),
        ('Kisumu', 'Kisumu'),
        ('Kitui', 'Kitui'),
        ('Kwale', 'Kwale'),
        ('Laikipia', 'Laikipia'),
        ('Lamu', 'Lamu'),
        ('Machakos', 'Machakos'),
        ('Makueni', 'Makueni'),
        ('Mandera', 'Mandera'),
        ('Marsabit', 'Marsabit'),
        ('Meru', 'Meru'),
        ('Migori', 'Migori'),
        ('Mombasa', 'Mombasa'),
        ('Murang\'a', 'Murang\'a'),
        ('Nairobi', 'Nairobi'),
        ('Nakuru', 'Nakuru'),
        ('Nandi', 'Nandi'),
        ('Narok', 'Narok'),
        ('Nyamira', 'Nyamira'),
        ('Nyandarua', 'Nyandarua'),
        ('Nyeri', 'Nyeri'),
        ('Samburu', 'Samburu'),
        ('Siaya', 'Siaya'),
        ('Taita/Taveta', 'Taita/Taveta'),
        ('Tana River', 'Tana River'),
        ('Tharaka-Nithi', 'Tharaka-Nithi'),
        ('Trans Nzoia', 'Trans Nzoia'),
        ('Turkana', 'Turkana'),
        ('Uasin Gishu', 'Uasin Gishu'),
        ('Vihiga', 'Vihiga'),
        ('Wajir', 'Wajir'),
        ('West Pokot', 'West Pokot')
    ])
    preferred_date = DateField('Preferred Date', validators=[DataRequired()])
    previous_evaluation = SelectField('Previous Evaluation', choices=[
        ('yes', 'Yes'),
        ('no', 'No')
    ])
    last_evaluation_date = DateField('Last Evaluation Date')
    notes = TextAreaField('Additional Notes')
    submit = SubmitField('Book Evaluation')

class EvaluationFormForm(FlaskForm):
    # Location and Date
    location = StringField('Location', validators=[DataRequired()])
    evaluation_date = DateField('Evaluation Date', validators=[DataRequired()])

    # Section 1: General Compliance
    contractor_license = BooleanField('Electrical contractor possesses a valid license')
    contractor_license_remarks = TextAreaField('Remarks')
    design_compliance = BooleanField('Electrical work complies with approved design')
    design_compliance_remarks = TextAreaField('Remarks')
    documentation = BooleanField('Adequate documentation of electrical installations')
    documentation_remarks = TextAreaField('Remarks')
    testing_records = BooleanField('Inspection and testing records available')
    testing_records_remarks = TextAreaField('Remarks')
    wiring_regulations = BooleanField('Compliance with BS 7671 wiring regulations')
    wiring_regulations_remarks = TextAreaField('Remarks')

    # Section 2: Electrical System Safety
    circuit_breakers = BooleanField('Circuit breakers and fuses are properly rated')
    circuit_breakers_remarks = TextAreaField('Remarks')
    earthing_bonding = BooleanField('Earthing and bonding properly implemented')
    earthing_bonding_remarks = TextAreaField('Remarks')
    exposed_wires = BooleanField('No exposed live wires or damaged cables')
    exposed_wires_remarks = TextAreaField('Remarks')
    rcd_installed = BooleanField('Residual Current Devices (RCDs) installed')
    rcd_installed_remarks = TextAreaField('Remarks')
    panel_labeling = BooleanField('Electrical panels are properly labeled')
    panel_labeling_remarks = TextAreaField('Remarks')

    # Section 3: Workplace Safety & Equipment Compliance
    equipment_inspection = BooleanField('Electrical equipment inspected and maintained')
    equipment_inspection_remarks = TextAreaField('Remarks')
    safety_signage = BooleanField('Proper signage and warning labels present')
    safety_signage_remarks = TextAreaField('Remarks')
    emergency_switches = BooleanField('Emergency shut-off switches are accessible')
    emergency_switches_remarks = TextAreaField('Remarks')
    circuit_loading = BooleanField('No overloading of circuits')
    circuit_loading_remarks = TextAreaField('Remarks')
    safety_procedures = BooleanField('Safety procedures for electrical emergencies')
    safety_procedures_remarks = TextAreaField('Remarks')

    # Section 4: Final Assessment
    overall_rating = SelectField('Overall Compliance Rating',
                                 choices=[('Excellent', 'Excellent'),
                                          ('Satisfactory', 'Satisfactory'),
                                          ('Needs Improvement', 'Needs Improvement'),
                                          ('Non-Compliant', 'Non-Compliant')],
                                 validators=[DataRequired()])
    corrective_actions = TextAreaField('Immediate Corrective Actions Required')
    additional_comments = TextAreaField('Additional Comments')
    evaluator_signature = StringField('Evaluator Signature', validators=[DataRequired()])

    submit = SubmitField('Submit Evaluation')

class IssueReportForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    issue_type = SelectField('Issue Type', choices=[
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('technical', 'Technical Issue'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    steps_to_reproduce = TextAreaField('Steps to Reproduce (if applicable)')
    submit = SubmitField('Submit Report')

class ReportForm(FlaskForm):
    report_file = FileField('Report File', validators=[DataRequired()])
    submit = SubmitField('Submit Report')
