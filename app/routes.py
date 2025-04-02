from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, get_flashed_messages, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Evaluation, Report, Payment, EvaluationForm, IssueReport
from app.forms import LoginForm, RegistrationForm, EvaluationBookingForm, EvaluationFormForm, ReportForm, IssueReportForm
from datetime import datetime
import os
from functools import wraps
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Define Blueprint
main = Blueprint('main', __name__)

def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.Role != 'Client':
            flash('Access denied. This area is for clients only.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def evaluator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.Role != 'Evaluator':
            flash('Access denied. This area is for evaluators only.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.Role != 'Admin':
            flash('Access denied. This area is for administrators only.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def home():
    # Clear any existing flash messages when returning to home
    if not current_user.is_authenticated:
        get_flashed_messages()  # This will clear the messages without displaying them
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(Email=form.email.data).first()
        if user and check_password_hash(user.PasswordHash, form.password.data):
            login_user(user)
            flash('Successfully logged in!', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.home'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        # Capitalize the role for database consistency
        role = form.role.data.capitalize()
        user = User(Name=form.name.data, Email=form.email.data, PasswordHash=hashed_password, Role=role)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/evaluations')
@login_required
def evaluations():
    if current_user.Role == 'Client':
        # Show client's evaluations
        evaluations = Evaluation.query.filter_by(ClientID=current_user.UserID).all()
        return render_template('evaluations.html', evaluations=evaluations)
    elif current_user.Role == 'Evaluator':
        # Show available and assigned evaluations
        evaluations = Evaluation.query.filter(
            (Evaluation.Status == 'Pending') |  # Show all pending evaluations
            ((Evaluation.Status.in_(['In Progress', 'Completed'])) & (Evaluation.EvaluatorID == current_user.UserID))  # Show only assigned non-pending evaluations
        ).order_by(Evaluation.CreatedAt.desc()).all()
        return render_template('evaluator_evaluations.html', evaluations=evaluations)
    else:
        abort(403)  # Forbidden for other roles

@main.route('/book-evaluation', methods=['GET', 'POST'])
@login_required
@client_required
def book_evaluation():
    form = EvaluationBookingForm()
    if form.validate_on_submit():
        # Combine address components
        full_address = f"{form.street_address.data}\n{form.town.data}\n{form.county.data}"
        
        try:
            evaluation = Evaluation(
                ClientID=current_user.UserID,
                Status='Pending',
                Comments=f"""
Property Type: {form.property_type.data}
Property Address: {full_address}
Preferred Date: {form.preferred_date.data}
Previous Evaluation: {form.previous_evaluation.data}
Last Evaluation Date: {form.last_evaluation_date.data if form.previous_evaluation.data == 'yes' else 'N/A'}
Additional Notes: {form.notes.data}
                """.strip(),
                CreatedAt=datetime.utcnow()
            )
            db.session.add(evaluation)
            db.session.commit()
            flash('Evaluation booked successfully! We will contact you to confirm the appointment.', 'success')
            return redirect(url_for('main.evaluations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error booking evaluation: {str(e)}', 'danger')
            
    return render_template('book_evaluation.html', form=form)

@main.route('/accept-evaluation/<int:evaluation_id>')
@login_required
@evaluator_required
def accept_evaluation(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    if evaluation.Status != 'Pending':
        flash('This evaluation is no longer available.', 'warning')
        return redirect(url_for('main.evaluations'))
    
    evaluation.EvaluatorID = current_user.UserID
    evaluation.Status = 'In Progress'  # Changed from 'Assigned' to 'In Progress'
    evaluation.AssignedDate = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Evaluation accepted successfully. You can now fill out the evaluation form.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while accepting the evaluation.', 'danger')
    
    return redirect(url_for('main.evaluations'))

@main.route('/complete-evaluation/<int:evaluation_id>')
@login_required
@evaluator_required
def complete_evaluation(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    if evaluation.EvaluatorID != current_user.UserID:
        flash('You can only complete evaluations assigned to you.', 'danger')
        return redirect(url_for('main.evaluations'))
    
    if evaluation.Status != 'In Progress':
        flash('Only in-progress evaluations can be completed.', 'warning')
        return redirect(url_for('main.evaluations'))
    
    evaluation.Status = 'Completed'
    db.session.commit()
    flash('Evaluation marked as completed.', 'success')
    return redirect(url_for('main.evaluations'))

@main.route('/reports')
@login_required
def reports():
    if current_user.Role == 'Client':
        reports = Report.query.join(Evaluation).filter(Evaluation.ClientID == current_user.UserID).all()
    elif current_user.Role == 'Evaluator':
        reports = Report.query.join(Evaluation).filter(Evaluation.EvaluatorID == current_user.UserID).all()
    else:
        reports = []
    return render_template('reports.html', reports=reports)

@main.route('/payments')
@login_required
@client_required
def payments():
    payments = Payment.query.filter_by(ClientID=current_user.UserID).all()
    return render_template('payments.html', payments=payments)

@main.route('/download_report/<int:report_id>')
@login_required
def download_report(report_id):
    # Get the report and verify it belongs to the current user
    report_query = Report.query.join(Evaluation)
    if current_user.Role == 'Client':
        report = report_query.filter(
            Report.ReportID == report_id,
            Evaluation.ClientID == current_user.UserID
        ).first_or_404()
    elif current_user.Role == 'Evaluator':
        report = report_query.filter(
            Report.ReportID == report_id,
            Evaluation.EvaluatorID == current_user.UserID
        ).first_or_404()
    else:
        abort(403)

    # Check if the file exists
    if not os.path.exists(report.ReportFilePath):
        flash('Report file not found.', 'error')
        return redirect(url_for('main.reports'))

    # Get the directory and filename from the path
    directory = os.path.dirname(report.ReportFilePath)
    filename = os.path.basename(report.ReportFilePath)

    try:
        # Return the file as a download
        return send_from_directory(
            directory,
            filename,
            as_attachment=True,
            download_name=f'report_{report.ReportID}_{filename}'
        )
    except Exception as e:
        flash('Error downloading report: ' + str(e), 'error')
        return redirect(url_for('main.reports'))

@main.route('/fill-evaluation-form/<int:evaluation_id>', methods=['GET', 'POST'])
@login_required
@evaluator_required
def fill_evaluation_form(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    # Check if evaluator is assigned to this evaluation
    if evaluation.EvaluatorID != current_user.UserID:
        flash('You can only fill evaluation forms for evaluations assigned to you.', 'danger')
        return redirect(url_for('main.evaluations'))
    
    # Check if evaluation is in progress
    if evaluation.Status != 'In Progress':
        flash('This evaluation is not in progress.', 'warning')
        return redirect(url_for('main.evaluations'))
    
    # Check if form already exists
    if evaluation.evaluation_form:
        flash('Evaluation form has already been submitted.', 'warning')
        return redirect(url_for('main.view_evaluation_form', evaluation_id=evaluation_id))
    
    form = EvaluationFormForm()
    if form.validate_on_submit():
        print("Form validation passed")  # Debug log
        try:
            # First create and save the evaluation form
            evaluation_form = EvaluationForm(
                EvaluationID=evaluation_id,
                Location=form.location.data,
                EvaluationDate=form.evaluation_date.data,
                
                # Section 1
                contractor_license=form.contractor_license.data,
                contractor_license_remarks=form.contractor_license_remarks.data,
                design_compliance=form.design_compliance.data,
                design_compliance_remarks=form.design_compliance_remarks.data,
                documentation=form.documentation.data,
                documentation_remarks=form.documentation_remarks.data,
                testing_records=form.testing_records.data,
                testing_records_remarks=form.testing_records_remarks.data,
                wiring_regulations=form.wiring_regulations.data,
                wiring_regulations_remarks=form.wiring_regulations_remarks.data,
                
                # Section 2
                circuit_breakers=form.circuit_breakers.data,
                circuit_breakers_remarks=form.circuit_breakers_remarks.data,
                earthing_bonding=form.earthing_bonding.data,
                earthing_bonding_remarks=form.earthing_bonding_remarks.data,
                exposed_wires=form.exposed_wires.data,
                exposed_wires_remarks=form.exposed_wires_remarks.data,
                rcd_installed=form.rcd_installed.data,
                rcd_installed_remarks=form.rcd_installed_remarks.data,
                panel_labeling=form.panel_labeling.data,
                panel_labeling_remarks=form.panel_labeling_remarks.data,
                
                # Section 3
                equipment_inspection=form.equipment_inspection.data,
                equipment_inspection_remarks=form.equipment_inspection_remarks.data,
                safety_signage=form.safety_signage.data,
                safety_signage_remarks=form.safety_signage_remarks.data,
                emergency_switches=form.emergency_switches.data,
                emergency_switches_remarks=form.emergency_switches_remarks.data,
                circuit_loading=form.circuit_loading.data,
                circuit_loading_remarks=form.circuit_loading_remarks.data,
                safety_procedures=form.safety_procedures.data,
                safety_procedures_remarks=form.safety_procedures_remarks.data,
                
                # Section 4
                overall_rating=form.overall_rating.data,
                corrective_actions=form.corrective_actions.data,
                additional_comments=form.additional_comments.data,
                evaluator_signature=form.evaluator_signature.data,
                signed_date=datetime.now().date()
            )
            
            print("Created evaluation form object")  # Debug log
            db.session.add(evaluation_form)
            print("Added form to session")  # Debug log
            
            try:
                db.session.flush()
                print("Session flush successful")  # Debug log
            except Exception as flush_error:
                print(f"Flush error: {str(flush_error)}")  # Debug log
                raise flush_error
            
            # Generate report content
            print("Generating report...")  # Debug log
            report_content = generate_evaluation_report(evaluation_form)
            
            # Create report file
            report_filename = f'evaluation_report_{evaluation_id}.pdf'
            report_path = os.path.join(current_app.config['REPORT_UPLOAD_FOLDER'], report_filename)
            print(f"Report will be saved to: {report_path}")  # Debug log
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            # Save PDF
            print("Saving PDF...")  # Debug log
            save_report_to_pdf(report_content, report_path)
            print("PDF saved successfully")  # Debug log
            
            # Create Report record
            report = Report(
                EvaluationID=evaluation_id,
                ReportFilePath=report_path
            )
            db.session.add(report)
            print("Added report to session")  # Debug log
            
            # Update evaluation status
            evaluation.Status = 'Completed'
            print("Updated evaluation status")  # Debug log
            
            # Commit all changes
            db.session.commit()
            print("All changes committed successfully")  # Debug log
            
            flash('Evaluation form submitted and report generated successfully!', 'success')
            return redirect(url_for('main.view_evaluation_form', evaluation_id=evaluation_id))
            
        except Exception as e:
            print(f"Error details: {str(e)}")  # Debug log
            db.session.rollback()
            flash(f'Error saving the evaluation form: {str(e)}', 'danger')
            return render_template('fill_evaluation_form.html', form=form, evaluation=evaluation)
    else:
        print("Form validation failed")  # Debug log
        print("Form errors:", form.errors)  # Debug log
    
    # Pre-fill form with evaluation and user data
    form.location.data = evaluation.Comments.split('\nProperty Address: ')[1].split('\n')[0]
    return render_template('fill_evaluation_form.html', form=form, evaluation=evaluation)

@main.route('/view-evaluation-form/<int:evaluation_id>')
@login_required
def view_evaluation_form(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    # Check if user has permission to view this form
    if not (current_user.Role == 'Admin' or 
            (current_user.Role == 'Client' and evaluation.ClientID == current_user.UserID) or
            (current_user.Role == 'Evaluator' and evaluation.EvaluatorID == current_user.UserID)):
        abort(403)
    
    if not evaluation.evaluation_form:
        flash('Evaluation form has not been submitted yet.', 'info')
        return redirect(url_for('main.evaluations'))
    
    return render_template('view_evaluation_form.html', evaluation=evaluation, form=evaluation.evaluation_form)

def generate_evaluation_report(evaluation_form):
    """Generate a formatted report from the evaluation form data"""
    report_content = f"""
    ELECTROPRO Electrical Safety Compliance Report
    
    Evaluation ID: {evaluation_form.EvaluationID}
    Location: {evaluation_form.Location}
    Date: {evaluation_form.EvaluationDate}
    
    1. General Compliance
    --------------------
    - Electrical Contractor License: {'✓' if evaluation_form.contractor_license else '✗'}
      Remarks: {evaluation_form.contractor_license_remarks}
    
    - Design Compliance: {'✓' if evaluation_form.design_compliance else '✗'}
      Remarks: {evaluation_form.design_compliance_remarks}
    
    - Documentation: {'✓' if evaluation_form.documentation else '✗'}
      Remarks: {evaluation_form.documentation_remarks}
    
    - Testing Records: {'✓' if evaluation_form.testing_records else '✗'}
      Remarks: {evaluation_form.testing_records_remarks}
    
    - Wiring Regulations: {'✓' if evaluation_form.wiring_regulations else '✗'}
      Remarks: {evaluation_form.wiring_regulations_remarks}
    
    2. Electrical System Safety
    -------------------------
    - Circuit Breakers: {'✓' if evaluation_form.circuit_breakers else '✗'}
      Remarks: {evaluation_form.circuit_breakers_remarks}
    
    - Earthing and Bonding: {'✓' if evaluation_form.earthing_bonding else '✗'}
      Remarks: {evaluation_form.earthing_bonding_remarks}
    
    - Exposed Wires: {'✓' if evaluation_form.exposed_wires else '✗'}
      Remarks: {evaluation_form.exposed_wires_remarks}
    
    - RCD Installation: {'✓' if evaluation_form.rcd_installed else '✗'}
      Remarks: {evaluation_form.rcd_installed_remarks}
    
    - Panel Labeling: {'✓' if evaluation_form.panel_labeling else '✗'}
      Remarks: {evaluation_form.panel_labeling_remarks}
    
    3. Workplace Safety & Equipment
    -----------------------------
    - Equipment Inspection: {'✓' if evaluation_form.equipment_inspection else '✗'}
      Remarks: {evaluation_form.equipment_inspection_remarks}
    
    - Safety Signage: {'✓' if evaluation_form.safety_signage else '✗'}
      Remarks: {evaluation_form.safety_signage_remarks}
    
    - Emergency Switches: {'✓' if evaluation_form.emergency_switches else '✗'}
      Remarks: {evaluation_form.emergency_switches_remarks}
    
    - Circuit Loading: {'✓' if evaluation_form.circuit_loading else '✗'}
      Remarks: {evaluation_form.circuit_loading_remarks}
    
    - Safety Procedures: {'✓' if evaluation_form.safety_procedures else '✗'}
      Remarks: {evaluation_form.safety_procedures_remarks}
    
    4. Final Assessment
    -----------------
    Overall Rating: {evaluation_form.overall_rating}
    
    Corrective Actions Required:
    {evaluation_form.corrective_actions}
    
    Additional Comments:
    {evaluation_form.additional_comments}
    
    Evaluator Signature: {evaluation_form.evaluator_signature}
    Date: {evaluation_form.signed_date}
    """
    return report_content

def save_report_to_pdf(content, filepath):
    """Save the report content to a PDF file with branded styling"""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.units import inch
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define brand colors
    navy_blue = colors.HexColor('#1a237e')
    yellow = colors.HexColor('#ffd700')
    grey = colors.HexColor('#424242')
    
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        textColor=navy_blue,
        spaceAfter=30
    )
    
    section_style = ParagraphStyle(
        'CustomSection',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=navy_blue,
        spaceBefore=20,
        spaceAfter=10,
        backColor=yellow.clone(alpha=0.2)
    )
    
    item_style = ParagraphStyle(
        'CustomItem',
        parent=styles['Normal'],
        fontSize=12,
        textColor=grey,
        leftIndent=20,
        spaceAfter=6,
        leading=16
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        textColor=grey,
        spaceAfter=12,
        leading=16
    )
    
    story = []
    
    # Process content line by line
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Clean up special characters
        line = line.replace('✓', 'Yes').replace('✗', 'No')
        
        if 'ELECTROPRO' in line:
            story.append(Paragraph(line, title_style))
            story.append(Spacer(1, 20))
        elif any(line.startswith(str(i)) for i in range(1, 5)):
            story.append(Spacer(1, 10))
            story.append(Paragraph(line, section_style))
            story.append(Spacer(1, 10))
        elif line.startswith(('-', '•')):
            story.append(Paragraph(line, item_style))
        elif line.startswith(('Evaluation ID:', 'Location:', 'Date:')):
            story.append(Paragraph(line, normal_style))
        elif 'Remarks:' in line:
            story.append(Paragraph(line, item_style))
        else:
            story.append(Paragraph(line, normal_style))
    
    doc.build(story)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/faqs')
def faqs():
    return render_template('faqs.html')

@main.route('/report-issue', methods=['GET', 'POST'])
def report_issue():
    form = IssueReportForm()
    if form.validate_on_submit():
        # Create new issue report
        issue_report = IssueReport(
            Name=form.name.data,
            Email=form.email.data,
            IssueType=form.issue_type.data,
            Description=form.description.data,
            StepsToReproduce=form.steps_to_reproduce.data,
            Status='New'
        )
        
        try:
            db.session.add(issue_report)
            db.session.commit()
            flash('Thank you for reporting the issue. Our team will review it shortly.', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your report. Please try again.', 'danger')
            return render_template('report_issue.html', form=form)
            
    return render_template('report_issue.html', form=form)

@main.route('/admin/issues')
@login_required
@admin_required
def admin_issues():
    issues = IssueReport.query.order_by(IssueReport.CreatedAt.desc()).all()
    return render_template('admin/issues.html', issues=issues)

@main.route('/admin/issues/<int:issue_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_issue_detail(issue_id):
    issue = IssueReport.query.get_or_404(issue_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_status':
            new_status = request.form.get('status')
            if new_status in ['New', 'In Progress', 'Resolved', 'Closed']:
                issue.Status = new_status
                if new_status in ['Resolved', 'Closed']:
                    issue.ResolvedAt = datetime.utcnow()
                    issue.Resolution = request.form.get('resolution')
                db.session.commit()
                flash('Issue status updated successfully.', 'success')
                return redirect(url_for('main.admin_issue_detail', issue_id=issue_id))
        
        elif action == 'add_comment':
            comment = request.form.get('comment')
            if comment:
                # Here you could add a comment system if needed
                flash('Comment added successfully.', 'success')
                return redirect(url_for('main.admin_issue_detail', issue_id=issue_id))
    
    return render_template('admin/issue_detail.html', issue=issue)

@main.route('/system/access', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if current_user.Role == 'Admin':
            return redirect(url_for('main.admin_issues'))
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(Email=form.email.data).first()
        if user and check_password_hash(user.PasswordHash, form.password.data):
            if user.Role == 'Admin':
                login_user(user)
                flash('Admin access granted.', 'success')
                return redirect(url_for('main.admin_issues'))
            else:
                flash('Access denied. Admin privileges required.', 'danger')
        else:
            flash('Invalid email or password', 'danger')
    return render_template('admin/login.html', form=form)
