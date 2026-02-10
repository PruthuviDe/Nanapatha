from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import os
from models import db, User, StudentProfile, TeacherProfile, Batch, RegistrationRequest, Classroom, ClassSession

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nanapatha.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Admin Dashboard Routes
@app.route('/')
def admin_dashboard():
    """Admin Dashboard - main overview page"""
    # Get summary statistics
    total_students = User.query.filter_by(role='student', status='active').count()
    total_teachers = User.query.filter_by(role='teacher', status='active').count()
    pending_registrations = RegistrationRequest.query.filter_by(status='pending').count()
    
    # Get recent pending registrations
    recent_registrations = RegistrationRequest.query.filter_by(status='pending').order_by(RegistrationRequest.submitted_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         total_students=total_students,
                         total_teachers=total_teachers,
                         pending_registrations=pending_registrations,
                         recent_registrations=recent_registrations)

@app.route('/admin/profile')
def admin_profile():
    """Admin Profile Management"""
    # For now, we'll use static admin data
    # In a real application, this would come from the authenticated user
    admin_data = {
        'name': 'William',
        'email': 'admin@nanapatha.com',
        'role': 'Super Admin',
        'joined': 'January 15, 2023',
        'avatar': 'W',
        'phone': '+1 (555) 123-4567',
        'department': 'Administration',
        'permissions': ['Full Access', 'User Management', 'System Settings', 'Reports']
    }
    
    return render_template('admin/profile.html', admin=admin_data)

@app.route('/admin/registrations')
def admin_registrations():
    """Admin Registrations List - view all pending registrations"""
    status_filter = request.args.get('status', 'pending')
    search_query = request.args.get('search', '')
    type_filter = request.args.get('filter', 'all')  # New filter for registration type
    
    query = RegistrationRequest.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Filter by registration type (existing/new)
    if type_filter == 'existing':
        query = query.filter_by(registration_type='existing')
    elif type_filter == 'new':
        query = query.filter_by(registration_type='new')
    
    if search_query:
        query = query.filter(
            (RegistrationRequest.name.contains(search_query)) |
            (RegistrationRequest.email.contains(search_query))
        )
    
    registrations = query.order_by(RegistrationRequest.submitted_at.desc()).all()
    
    return render_template('admin/registrations.html', 
                         registrations=registrations,
                         status_filter=status_filter,
                         search_query=search_query,
                         type_filter=type_filter)

@app.route('/admin/registrations/<int:reg_id>')
def admin_registration_detail(reg_id):
    """Admin Registration Detail - review specific registration request"""
    registration = RegistrationRequest.query.get_or_404(reg_id)
    
    # Get related batch if selected
    selected_batch = None
    if registration.selected_batch_id:
        selected_batch = Batch.query.get(registration.selected_batch_id)
    
    return render_template('admin/registration_detail.html', 
                         registration=registration,
                         selected_batch=selected_batch)

@app.route('/admin/registrations/<int:reg_id>/accept', methods=['POST'])
def accept_registration(reg_id):
    """Accept a registration request and create student account"""
    registration = RegistrationRequest.query.get_or_404(reg_id)
    
    if registration.status != 'pending':
        flash('Registration has already been processed', 'error')
        return redirect(url_for('admin_registration_detail', reg_id=reg_id))
    
    # Create user account
    user = User(
        name=registration.name,
        email=registration.email,
        role='student',
        status='active',
        temp_password='temp123',  # In real app, generate secure temp password
        created_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.flush()  # Get user ID
    
    # Create student profile
    student_profile = StudentProfile(
        user_id=user.id,
        dob=registration.dob,
        grade=registration.grade,
        contact_number=registration.mobile,
        address=registration.address,
        class_type=registration.class_type,
        batch_id=registration.selected_batch_id,
        student_id_number=registration.student_id_number
    )
    db.session.add(student_profile)
    
    # Update registration status
    registration.status = 'accepted'
    registration.admin_note = f"Accepted by admin on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    
    db.session.commit()
    
    flash(f'Registration accepted! Student account created for {registration.name}. Temporary password: temp123', 'success')
    return redirect(url_for('admin_registrations'))

@app.route('/admin/registrations/<int:reg_id>/reject', methods=['POST'])
def reject_registration(reg_id):
    """Reject a registration request with reason"""
    registration = RegistrationRequest.query.get_or_404(reg_id)
    reason = request.form.get('reason', '')
    
    if not reason:
        flash('Rejection reason is required', 'error')
        return redirect(url_for('admin_registration_detail', reg_id=reg_id))
    
    registration.status = 'rejected'
    registration.admin_note = f"Rejected: {reason}"
    
    db.session.commit()
    
    flash(f'Registration rejected for {registration.name}', 'success')
    return redirect(url_for('admin_registrations'))

@app.route('/admin/registrations/<int:reg_id>/claim', methods=['POST'])
def claim_registration(reg_id):
    """Claim a registration for review"""
    registration = RegistrationRequest.query.get_or_404(reg_id)
    
    registration.claimed_by = 'Admin User'  # In real app, use current admin user
    registration.claimed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Registration claimed'})

@app.route('/admin/registrations/<int:reg_id>/mark-paid', methods=['POST'])
def mark_paid(reg_id):
    """Mark registration payment as received"""
    registration = RegistrationRequest.query.get_or_404(reg_id)
    
    registration.payment_status = 'paid'
    
    db.session.commit()
    
    flash('Payment marked as received', 'success')
    return redirect(url_for('admin_registration_detail', reg_id=reg_id))

# Student Registration Routes (for testing)
@app.route('/student/register/new')
def student_register_new():
    """New Student Registration Form"""
    batches = Batch.query.all()
    return render_template('student/register_new.html', batches=batches)

@app.route('/student/register/new', methods=['POST'])
def student_register_new_submit():
    """Submit New Student Registration"""
    registration = RegistrationRequest(
        name=request.form['name'],
        email=request.form['email'],
        mobile=request.form['mobile'],
        address=request.form['address'],
        dob=datetime.strptime(request.form['dob'], '%Y-%m-%d').date(),
        grade=request.form['grade'],
        class_type=request.form['class_type'],
        selected_batch_id=int(request.form['selected_batch']) if request.form['selected_batch'] else None,
        registration_type='new',
        payment_status='pending',
        status='pending',
        submitted_at=datetime.utcnow()
    )
    
    db.session.add(registration)
    db.session.commit()
    
    flash('Registration submitted successfully! Please wait for admin approval.', 'success')
    return redirect(url_for('student_register_new'))

@app.route('/student/register/existing')
def student_register_existing():
    """Existing Student Registration Form"""
    return render_template('student/register_existing.html')

@app.route('/student/register/existing', methods=['POST'])
def student_register_existing_submit():
    """Submit Existing Student Registration"""
    registration = RegistrationRequest(
        name=request.form['name'],
        email=request.form['email'],
        mobile=request.form.get('mobile'),
        student_id_number=request.form['student_id'],
        registration_type='existing',
        payment_status='paid',  # Existing students already paid
        status='pending',
        submitted_at=datetime.utcnow()
    )
    
    db.session.add(registration)
    db.session.commit()
    
    flash('Registration submitted successfully! Please wait for admin approval.', 'success')
    return redirect(url_for('student_register_existing'))

# Students Management Routes
@app.route('/admin/students')
def admin_students():
    """Admin Students List"""
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    
    query = User.query.filter_by(role='student')
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(
            db.or_(
                User.name.contains(search_query),
                User.email.contains(search_query)
            )
        )
    
    students = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/students.html', 
                         students=students,
                         status_filter=status_filter,
                         search_query=search_query)

@app.route('/admin/students/<int:student_id>')
def admin_student_detail(student_id):
    """Admin Student Detail View"""
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    return render_template('admin/student_detail.html', student=student)

@app.route('/admin/students/<int:student_id>/edit')
def admin_student_edit(student_id):
    """Edit Student Form"""
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    batches = Batch.query.all()
    return render_template('admin/student_edit.html', 
                         student=student, 
                         batches=batches,
                         today=datetime.now().date())

@app.route('/admin/students/<int:student_id>/edit', methods=['POST'])
def admin_student_edit_submit(student_id):
    """Update Student"""
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    
    # Update user information
    student.name = request.form['name']
    student.email = request.form['email']
    student.phone = request.form.get('phone')
    student.updated_at = datetime.utcnow()
    
    # Update or create student profile
    if not student.student_profile:
        student.student_profile = StudentProfile(user_id=student.id)
    
    profile = student.student_profile
    profile.grade = request.form.get('grade')
    profile.contact_number = request.form.get('contact_number')
    profile.address = request.form.get('address')
    profile.class_type = request.form.get('class_type')
    
    # Handle batch assignment
    batch_id = request.form.get('batch_id')
    if batch_id:
        profile.batch_id = int(batch_id)
    else:
        profile.batch_id = None
    
    # Handle date of birth
    dob_str = request.form.get('dob')
    if dob_str:
        from datetime import datetime
        profile.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    
    db.session.commit()
    flash(f'Student {student.name} updated successfully!', 'success')
    return redirect(url_for('admin_student_detail', student_id=student.id))

@app.route('/admin/students/<int:student_id>/deactivate', methods=['POST'])
def admin_student_deactivate(student_id):
    """Deactivate Student"""
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    student.status = 'inactive'
    student.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'Student {student.name} has been deactivated.', 'info')
    return redirect(url_for('admin_students'))

@app.route('/admin/students/create')
def admin_student_create():
    """Create New Student Form"""
    batches = Batch.query.all()
    return render_template('admin/student_create.html', batches=batches)

@app.route('/admin/students/create', methods=['POST'])
def admin_student_create_submit():
    """Create New Student"""
    user = User(
        name=request.form['name'],
        email=request.form['email'],
        phone=request.form.get('phone'),
        role='student',
        status=request.form.get('status', 'active'),
        temp_password='temp123',
        created_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.flush()
    
    student_profile = StudentProfile(
        user_id=user.id,
        grade=request.form.get('grade'),
        school=request.form.get('school'),
        guardian_name=request.form.get('guardian_name'),
        guardian_phone=request.form.get('guardian_phone'),
        emergency_contact=request.form.get('emergency_contact'),
        batch_id=int(request.form['batch_id']) if request.form.get('batch_id') else None,
        student_id_number=request.form.get('student_id_number') or f"STU{user.id:06d}"
    )
    db.session.add(student_profile)
    db.session.commit()
    
    flash(f'Student {user.name} created successfully!', 'success')
    return redirect(url_for('admin_students'))

# Student-Batch Assignment Routes
@app.route('/admin/students/<int:student_id>/assign-batch')
def admin_student_assign_batch(student_id):
    """Student Batch Assignment Form"""
    student = StudentProfile.query.get_or_404(student_id)
    batches = Batch.query.filter_by(is_active=True).all()
    return render_template('admin/student_assign_batch.html', student=student, batches=batches)

@app.route('/admin/students/<int:student_id>/assign-batch', methods=['POST'])
def admin_student_assign_batch_submit(student_id):
    """Assign Student to Batch"""
    student = StudentProfile.query.get_or_404(student_id)
    old_batch = student.batch
    new_batch_id = request.form.get('batch_id')
    
    if new_batch_id:
        new_batch = Batch.query.get(int(new_batch_id))
        if new_batch and new_batch.current_enrollment < new_batch.capacity:
            # Update student's batch
            student.batch_id = int(new_batch_id)
            
            # Update enrollment counts
            if old_batch:
                old_batch.current_enrollment = max(0, old_batch.current_enrollment - 1)
            new_batch.current_enrollment += 1
            
            db.session.commit()
            flash(f'Student {student.user.name} assigned to batch {new_batch.name}!', 'success')
        else:
            flash('Selected batch is full or invalid!', 'error')
    else:
        # Remove from current batch
        if old_batch:
            old_batch.current_enrollment = max(0, old_batch.current_enrollment - 1)
            student.batch_id = None
            db.session.commit()
            flash(f'Student {student.user.name} removed from batch!', 'info')
    
    return redirect(url_for('admin_students'))

@app.route('/admin/batches/<int:batch_id>/manage-students')
def admin_batch_manage_students(batch_id):
    """Batch Student Management"""
    batch = Batch.query.get_or_404(batch_id)
    current_students = StudentProfile.query.filter_by(batch_id=batch_id).all()
    # Get available students through User model join for status check
    available_students = StudentProfile.query.join(User).filter(
        StudentProfile.batch_id.is_(None),
        User.status == 'active'
    ).all()
    return render_template('admin/batch_manage_students.html', 
                         batch=batch, 
                         current_students=current_students,
                         available_students=available_students)

@app.route('/admin/batches/<int:batch_id>/add-student', methods=['POST'])
def admin_batch_add_student(batch_id):
    """Add Student to Batch"""
    batch = Batch.query.get_or_404(batch_id)
    student_id = request.form.get('student_id')
    
    if student_id and batch.current_enrollment < batch.capacity:
        student = StudentProfile.query.get(int(student_id))
        if student and not student.batch_id:
            student.batch_id = batch_id
            batch.current_enrollment += 1
            db.session.commit()
            flash(f'Student {student.user.name} added to batch {batch.name}!', 'success')
        else:
            flash('Student is already in a batch!', 'error')
    else:
        flash('Batch is full or invalid student!', 'error')
    
    return redirect(url_for('admin_batch_manage_students', batch_id=batch_id))

@app.route('/admin/batches/<int:batch_id>/remove-student/<int:student_id>', methods=['POST'])
def admin_batch_remove_student(batch_id, student_id):
    """Remove Student from Batch"""
    batch = Batch.query.get_or_404(batch_id)
    student = StudentProfile.query.get_or_404(student_id)
    
    if student.batch_id == batch_id:
        student.batch_id = None
        batch.current_enrollment = max(0, batch.current_enrollment - 1)
        db.session.commit()
        flash(f'Student {student.user.name} removed from batch {batch.name}!', 'info')
    
    return redirect(url_for('admin_batch_manage_students', batch_id=batch_id))

# Teachers Management Routes
@app.route('/admin/teachers')
def admin_teachers():
    """Admin Teachers List"""
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    
    query = User.query.filter_by(role='teacher')
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(
            db.or_(
                User.name.contains(search_query),
                User.email.contains(search_query)
            )
        )
    
    teachers = query.order_by(User.name).all()
    
    return render_template('admin/teachers.html', 
                         teachers=teachers,
                         search_query=search_query,
                         status_filter=status_filter)

@app.route('/admin/teachers/create')
def admin_teacher_create():
    """Create New Teacher Form"""
    batches = Batch.query.all()
    return render_template('admin/teacher_create.html', 
                         batches=batches,
                         today=datetime.now().date())

@app.route('/admin/teachers/create', methods=['POST'])
def admin_teacher_create_submit():
    """Create New Teacher"""
    user = User(
        name=request.form['name'],
        email=request.form['email'],
        phone=request.form.get('phone'),
        role='teacher',
        status=request.form.get('status', 'active'),
        created_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.flush()
    
    teacher_profile = TeacherProfile(
        user_id=user.id,
        subject_specialization=request.form.get('subject_specialization'),
        experience_years=int(request.form.get('experience_years', 0)) if request.form.get('experience_years') else None,
        qualifications=request.form.get('qualifications'),
        employee_id=request.form.get('employee_id') or f"TEA{user.id:06d}",
        bio=request.form.get('bio')
    )
    db.session.add(teacher_profile)
    db.session.commit()
    
    flash(f'Teacher {user.name} created successfully!', 'success')
    return redirect(url_for('admin_teachers'))

@app.route('/admin/teachers/<int:teacher_id>/edit')
def admin_teacher_edit(teacher_id):
    """Edit Teacher Form"""
    teacher = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
    return render_template('admin/teacher_edit.html', 
                         teacher=teacher,
                         today=datetime.now().date())

@app.route('/admin/teachers/<int:teacher_id>/edit', methods=['POST'])
def admin_teacher_edit_submit(teacher_id):
    """Update Teacher"""
    teacher = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
    
    # Update user information
    teacher.name = request.form['name']
    teacher.email = request.form['email']
    teacher.phone = request.form.get('phone')
    teacher.updated_at = datetime.utcnow()
    
    # Update or create teacher profile
    if not teacher.teacher_profile:
        teacher.teacher_profile = TeacherProfile(user_id=teacher.id)
    
    profile = teacher.teacher_profile
    
    # Handle subjects (multiple values)
    subjects = request.form.getlist('subjects')
    if subjects:
        profile.subjects = subjects
    else:
        profile.subjects = []
    
    profile.contact_number = request.form.get('contact_number')
    profile.bio = request.form.get('bio')
    profile.active_flag = True  # Keep active when editing
    
    db.session.commit()
    flash(f'Teacher {teacher.name} updated successfully!', 'success')
    return redirect(url_for('admin_teacher_detail', teacher_id=teacher.id))

@app.route('/admin/teachers/<int:teacher_id>/deactivate', methods=['POST'])
def admin_teacher_deactivate(teacher_id):
    """Deactivate Teacher"""
    teacher = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
    teacher.status = 'inactive'
    teacher.updated_at = datetime.utcnow()
    
    # Also deactivate teacher profile
    if teacher.teacher_profile:
        teacher.teacher_profile.active_flag = False
    
    db.session.commit()
    flash(f'Teacher {teacher.name} has been deactivated.', 'info')
    return redirect(url_for('admin_teachers'))

# Teacher-Batch Assignment Routes
@app.route('/admin/teachers/<int:teacher_id>/assign-batch')
def admin_teacher_assign_batch(teacher_id):
    """Teacher Batch Assignment Form"""
    teacher = TeacherProfile.query.get_or_404(teacher_id)
    batches = Batch.query.filter_by(is_active=True).all()
    return render_template('admin/teacher_assign_batch.html', teacher=teacher, batches=batches)

@app.route('/admin/teachers/<int:teacher_id>/assign-batch', methods=['POST'])
def admin_teacher_assign_batch_submit(teacher_id):
    """Assign Teacher to Batch"""
    teacher = TeacherProfile.query.get_or_404(teacher_id)
    batch_id = request.form.get('batch_id')
    
    if batch_id:
        batch = Batch.query.get(int(batch_id))
        if batch:
            # Remove teacher from previous batch if assigned
            old_batch = Batch.query.filter_by(teacher_id=teacher_id).first()
            if old_batch:
                old_batch.teacher_id = None
            
            # Assign to new batch
            batch.teacher_id = teacher_id
            db.session.commit()
            flash(f'Teacher {teacher.user.name} assigned to batch {batch.name}!', 'success')
        else:
            flash('Invalid batch selected!', 'error')
    else:
        # Remove from current batch
        current_batch = Batch.query.filter_by(teacher_id=teacher_id).first()
        if current_batch:
            current_batch.teacher_id = None
            db.session.commit()
            flash(f'Teacher {teacher.user.name} removed from batch assignment!', 'info')
    
    return redirect(url_for('admin_teachers'))

@app.route('/admin/teachers/<int:teacher_id>/teaching-load')
def admin_teacher_teaching_load(teacher_id):
    """Teacher Teaching Load Management"""
    teacher = TeacherProfile.query.get_or_404(teacher_id)
    assigned_batches = Batch.query.filter_by(teacher_id=teacher_id, is_active=True).all()
    available_batches = Batch.query.filter_by(teacher_id=None, is_active=True).all()
    
    # Calculate total students and hours
    total_students = sum(batch.current_enrollment for batch in assigned_batches)
    total_batches = len(assigned_batches)
    
    return render_template('admin/teacher_teaching_load.html', 
                         teacher=teacher, 
                         assigned_batches=assigned_batches,
                         available_batches=available_batches,
                         total_students=total_students,
                         total_batches=total_batches)

@app.route('/admin/batches/<int:batch_id>/assign-teacher')
def admin_batch_assign_teacher(batch_id):
    """Batch Teacher Assignment Form"""
    batch = Batch.query.get_or_404(batch_id)
    # Get active teachers through User model join
    teachers = TeacherProfile.query.join(User).filter(
        TeacherProfile.active_flag == True,
        User.status == 'active'
    ).all()
    return render_template('admin/batch_assign_teacher.html', batch=batch, teachers=teachers)

@app.route('/admin/batches/<int:batch_id>/assign-teacher', methods=['POST'])
def admin_batch_assign_teacher_submit(batch_id):
    """Assign Teacher to Batch"""
    batch = Batch.query.get_or_404(batch_id)
    teacher_id = request.form.get('teacher_id')
    
    if teacher_id:
        teacher = TeacherProfile.query.get(int(teacher_id))
        if teacher:
            # Remove previous assignment if exists
            if batch.teacher_id:
                old_teacher = TeacherProfile.query.get(batch.teacher_id)
                if old_teacher:
                    flash(f'Removed {old_teacher.user.name} from batch {batch.name}', 'info')
            
            batch.teacher_id = int(teacher_id)
            db.session.commit()
            flash(f'Teacher {teacher.user.name} assigned to batch {batch.name}!', 'success')
        else:
            flash('Invalid teacher selected!', 'error')
    else:
        # Remove current teacher
        if batch.teacher_id:
            old_teacher = TeacherProfile.query.get(batch.teacher_id)
            batch.teacher_id = None
            db.session.commit()
            if old_teacher:
                flash(f'Teacher {old_teacher.user.name} removed from batch {batch.name}!', 'info')
    
    return redirect(url_for('admin_batches'))

# Teacher Performance and Schedule Routes
@app.route('/admin/teachers/<int:teacher_id>/schedule')
def admin_teacher_schedule(teacher_id):
    """Teacher Schedule Management"""
    teacher = TeacherProfile.query.get_or_404(teacher_id)
    # Get teacher's assigned batches and their sessions
    assigned_batches = Batch.query.filter_by(teacher_id=teacher_id, is_active=True).all()
    # Get upcoming sessions for this teacher
    sessions = ClassSession.query.filter_by(teacher_user_id=teacher.user_id).all()
    return render_template('admin/teacher_schedule.html', 
                         teacher=teacher, 
                         assigned_batches=assigned_batches,
                         sessions=sessions)

@app.route('/admin/teachers/<int:teacher_id>/performance')
def admin_teacher_performance(teacher_id):
    """Teacher Performance Dashboard"""
    teacher = TeacherProfile.query.get_or_404(teacher_id)
    assigned_batches = Batch.query.filter_by(teacher_id=teacher_id, is_active=True).all()
    
    # Calculate performance metrics
    total_students = sum(batch.current_enrollment for batch in assigned_batches)
    total_sessions = ClassSession.query.filter_by(teacher_user_id=teacher.user_id).count()
    completed_sessions = ClassSession.query.filter_by(
        teacher_user_id=teacher.user_id, 
        status='completed'
    ).count()
    
    return render_template('admin/teacher_performance.html', 
                         teacher=teacher,
                         assigned_batches=assigned_batches,
                         total_students=total_students,
                         total_sessions=total_sessions,
                         completed_sessions=completed_sessions)

# Teachers Management Routes
@app.route('/admin/batches')
def admin_batches():
    """Admin Batches List"""
    search_query = request.args.get('search', '')
    subject_filter = request.args.get('subject', '')
    grade_filter = request.args.get('grade', '')
    status_filter = request.args.get('status', '')
    
    query = Batch.query
    
    if search_query:
        query = query.filter(Batch.name.contains(search_query))
    
    if subject_filter:
        query = query.filter_by(subject=subject_filter)
    
    if grade_filter:
        query = query.filter_by(grade_level=grade_filter)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    batches = query.order_by(Batch.created_at.desc()).all()
    
    return render_template('admin/batches.html', 
                         batches=batches,
                         search_query=search_query,
                         now=datetime.now())

@app.route('/admin/batches/create')
def admin_batch_create():
    """Create New Batch Form"""
    teachers = User.query.filter_by(role='teacher', status='active').all()
    return render_template('admin/batch_create.html', teachers=teachers)

@app.route('/admin/batches/create', methods=['POST'])
def admin_batch_create_submit():
    """Create New Batch"""
    batch = Batch(
        name=request.form['name'],
        grade=request.form['grade'],
        subject=request.form['subject'],
        capacity=int(request.form['capacity']),
        teacher_name=request.form['teacher_name'],
        class_type=request.form['class_type'],
        notes=request.form.get('notes'),
        created_at=datetime.utcnow()
    )
    
    db.session.add(batch)
    db.session.commit()
    
    flash(f'Batch {batch.name} created successfully!', 'success')
    return redirect(url_for('admin_batches'))

@app.route('/admin/batches/<int:batch_id>/edit')
def admin_batch_edit(batch_id):
    """Edit Batch Form"""
    batch = Batch.query.get_or_404(batch_id)
    teachers = User.query.filter_by(role='teacher', status='active').all()
    return render_template('admin/batch_edit.html', 
                         batch=batch, 
                         teachers=teachers)

@app.route('/admin/batches/<int:batch_id>/edit', methods=['POST'])
def admin_batch_edit_submit(batch_id):
    """Update Batch"""
    batch = Batch.query.get_or_404(batch_id)
    
    # Update batch information
    batch.name = request.form['name']
    batch.grade = request.form['grade']
    batch.subject = request.form['subject']
    batch.capacity = int(request.form['capacity'])
    batch.teacher_name = request.form['teacher_name']
    batch.class_type = request.form['class_type']
    batch.notes = request.form.get('notes')
    
    db.session.commit()
    flash(f'Batch {batch.name} updated successfully!', 'success')
    return redirect(url_for('admin_batch_detail', batch_id=batch.id))

@app.route('/admin/batches/<int:batch_id>/archive', methods=['POST'])
def admin_batch_archive(batch_id):
    """Archive Batch"""
    batch = Batch.query.get_or_404(batch_id)
    
    # For prototype, we'll just add a note that it's archived
    batch.notes = f"ARCHIVED: {batch.notes or ''}"
    
    db.session.commit()
    flash(f'Batch {batch.name} has been archived.', 'info')
    return redirect(url_for('admin_batches'))

# Classrooms Management Routes
@app.route('/admin/classrooms')
def admin_classrooms():
    """Admin Classrooms List"""
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Classroom.query
    
    if search_query:
        query = query.filter(
            db.or_(
                Classroom.name.contains(search_query),
                Classroom.location.contains(search_query) if Classroom.location else False
            )
        )
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    classrooms = query.order_by(Classroom.name).all()
    
    return render_template('admin/classrooms.html', 
                         classrooms=classrooms,
                         search_query=search_query)

@app.route('/admin/classrooms/create')
def admin_classroom_create():
    """Create New Classroom Form"""
    return render_template('admin/classroom_create.html')

@app.route('/admin/classrooms/create', methods=['POST'])
def admin_classroom_create_submit():
    """Create New Classroom"""
    classroom = Classroom(
        name=request.form['name'],
        capacity=int(request.form['capacity']),
        location=request.form.get('location'),
        equipment=equipment_string,
        notes=request.form.get('notes'),
        created_at=datetime.utcnow()
    )
    
    db.session.add(classroom)
    db.session.commit()
    
    flash(f'Classroom {classroom.name} created successfully!', 'success')
    return redirect(url_for('admin_classrooms'))

@app.route('/admin/classrooms/<int:classroom_id>/edit')
def admin_classroom_edit(classroom_id):
    """Edit Classroom Form"""
    classroom = Classroom.query.get_or_404(classroom_id)
    return render_template('admin/classroom_edit.html', classroom=classroom)

@app.route('/admin/classrooms/<int:classroom_id>/edit', methods=['POST'])
def admin_classroom_edit_submit(classroom_id):
    """Update Classroom"""
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # Update classroom information
    classroom.name = request.form['name']
    classroom.capacity = int(request.form['capacity'])
    classroom.location = request.form.get('location')
    classroom.notes = request.form.get('notes')
    
    db.session.commit()
    flash(f'Classroom {classroom.name} updated successfully!', 'success')
    return redirect(url_for('admin_classrooms'))

@app.route('/admin/classrooms/<int:classroom_id>/archive', methods=['POST'])
def admin_classroom_archive(classroom_id):
    """Archive Classroom"""
    classroom = Classroom.query.get_or_404(classroom_id)
    classroom.is_active = False
    db.session.commit()
    
    flash(f'Classroom {classroom.name} has been archived!', 'info')
    return redirect(url_for('admin_classrooms'))

# Schedule Management Routes
@app.route('/admin/schedule')
def admin_schedule():
    """Admin Schedule View"""
    from datetime import timedelta
    
    # Get current date or date from query parameter
    date_param = request.args.get('date')
    if date_param:
        current_date = datetime.strptime(date_param, '%Y-%m-%d').date()
    else:
        current_date = datetime.now().date()
    
    # Get sessions for the week
    week_start = current_date - timedelta(days=current_date.weekday())
    week_end = week_start + timedelta(days=6)
    
    sessions = ClassSession.query.filter(
        ClassSession.date >= week_start,
        ClassSession.date <= week_end
    ).all()
    
    # Get today's sessions
    today_sessions = ClassSession.query.filter_by(date=current_date).all()
    
    # Get active sessions
    now = datetime.now().time()
    active_sessions = [s for s in today_sessions if s.start_time <= now <= s.end_time]
    
    # Get upcoming sessions
    upcoming_sessions = [s for s in today_sessions if s.start_time > now]
    
    # Get data for filters
    teachers = User.query.filter_by(role='teacher', status='active').all()
    batches = Batch.query.all()
    classrooms = Classroom.query.all()
    
    return render_template('admin/schedule.html',
                         current_date=current_date,
                         sessions=sessions,
                         today_sessions=today_sessions,
                         active_sessions=active_sessions,
                         upcoming_sessions=upcoming_sessions,
                         teachers=teachers,
                         batches=batches,
                         classrooms=classrooms,
                         timedelta=timedelta)

@app.route('/admin/schedule/create')
def admin_schedule_create_form():
    """Create Session Form"""
    teachers = User.query.filter_by(role='teacher', status='active').all()
    batches = Batch.query.all()
    classrooms = Classroom.query.all()
    
    # Pre-fill form with query parameters
    date = request.args.get('date')
    time = request.args.get('time')
    
    return render_template('admin/schedule_create.html',
                         teachers=teachers,
                         batches=batches,
                         classrooms=classrooms,
                         prefill_date=date,
                         prefill_time=time)

@app.route('/admin/schedule/create', methods=['POST'])
def admin_schedule_create():
    """Create New Class Session"""
    session = ClassSession(
        batch_id=int(request.form['batch_id']) if request.form.get('batch_id') else None,
        teacher_user_id=int(request.form['teacher_id']) if request.form.get('teacher_id') else None,
        classroom_id=int(request.form['classroom_id']) if request.form.get('classroom_id') else None,
        date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
        start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
        end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
        topic=request.form.get('topic'),
        status='scheduled'
    )
    
    db.session.add(session)
    db.session.commit()
    
    flash('Class session scheduled successfully!', 'success')
    return redirect(url_for('admin_schedule'))

# Detail routes
@app.route('/admin/teachers/<int:teacher_id>')
def admin_teacher_detail(teacher_id):
    """Teacher Detail View"""
    teacher = User.query.get_or_404(teacher_id)
    return render_template('admin/teacher_detail.html', teacher=teacher)

@app.route('/admin/batches/<int:batch_id>')
def admin_batch_detail(batch_id):
    """Batch Detail View"""
    batch = Batch.query.get_or_404(batch_id)
    return render_template('admin/batch_detail.html', batch=batch)

@app.route('/admin/classrooms/<int:classroom_id>')
def admin_classroom_detail(classroom_id):
    """Classroom Detail View"""
    classroom = Classroom.query.get_or_404(classroom_id)
    return render_template('admin/classroom_detail.html', classroom=classroom)

def migrate_database():
    """Add missing columns to existing database"""
    try:
        # Check if columns exist and add them if they don't
        with db.engine.begin() as conn:
            # Add missing columns to batches table
            try:
                conn.execute(db.text("ALTER TABLE batches ADD COLUMN current_enrollment INTEGER DEFAULT 0"))
                # Update existing records to calculate current enrollment
                conn.execute(db.text("""
                    UPDATE batches SET current_enrollment = (
                        SELECT COUNT(*) FROM student_profiles 
                        WHERE student_profiles.batch_id = batches.id
                    ) WHERE current_enrollment IS NULL OR current_enrollment = 0
                """))
            except:
                pass  # Column already exists
            
            try:
                conn.execute(db.text("ALTER TABLE batches ADD COLUMN teacher_id INTEGER"))
            except:
                pass
                
            try:
                conn.execute(db.text("ALTER TABLE batches ADD COLUMN start_date DATE"))
            except:
                pass
                
            try:
                conn.execute(db.text("ALTER TABLE batches ADD COLUMN end_date DATE"))
            except:
                pass
                
            try:
                conn.execute(db.text("ALTER TABLE batches ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                # Set all existing batches as active
                conn.execute(db.text("UPDATE batches SET is_active = 1 WHERE is_active IS NULL"))
            except:
                pass
            
            # Add missing columns to classrooms table
            try:
                conn.execute(db.text("ALTER TABLE classrooms ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                # Set all existing classrooms as active
                conn.execute(db.text("UPDATE classrooms SET is_active = 1 WHERE is_active IS NULL"))
            except:
                pass  # Column already exists
                
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Database migration error: {e}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrate_database()
    app.run(debug=True)