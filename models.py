from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Numeric

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255))
    temp_password = db.Column(db.String(255))
    role = db.Column(db.Enum('student', 'teacher', 'admin', name='user_roles'), nullable=False)
    status = db.Column(db.Enum('pending', 'active', 'inactive', name='user_status'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False, cascade='all, delete-orphan')

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dob = db.Column(db.Date)
    grade = db.Column(db.String(10))
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    contact_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    class_type = db.Column(db.Enum('online', 'physical', 'both', name='class_types'))
    student_id_number = db.Column(db.String(50), unique=True)
    passport_photo_path = db.Column(db.String(255))
    student_id_card_path = db.Column(db.String(255))
    
    # Relationships
    batch = db.relationship('Batch', backref='students')

class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subjects = db.Column(db.JSON)  # Store as JSON array
    contact_number = db.Column(db.String(20))
    bio = db.Column(db.Text)
    active_flag = db.Column(db.Boolean, default=True)

class Batch(db.Model):
    __tablename__ = 'batches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.String(10))
    subject = db.Column(db.String(100))
    capacity = db.Column(db.Integer, default=30)
    current_enrollment = db.Column(db.Integer, default=0)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_profiles.id'))
    teacher_name = db.Column(db.String(255))  # Simplified for prototype
    class_type = db.Column(db.Enum('online', 'physical', 'both', name='class_types'))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('TeacherProfile', backref='assigned_batches')

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ClassSession(db.Model):
    __tablename__ = 'class_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'))
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    topic = db.Column(db.String(255))
    status = db.Column(db.Enum('scheduled', 'completed', 'cancelled', name='session_status'), default='scheduled')
    
    # Relationships
    batch = db.relationship('Batch', backref='sessions')
    teacher = db.relationship('User', backref='taught_sessions')
    classroom = db.relationship('Classroom', backref='sessions')

class RegistrationRequest(db.Model):
    __tablename__ = 'registration_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    mobile = db.Column(db.String(20))
    address = db.Column(db.Text)
    dob = db.Column(db.Date)
    grade = db.Column(db.String(10))
    class_type = db.Column(db.Enum('online', 'physical', 'both', name='class_types'))
    selected_batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    student_id_number = db.Column(db.String(50))  # For existing students
    
    # Registration metadata
    registration_type = db.Column(db.Enum('new', 'existing', name='registration_types'), nullable=False)
    payment_status = db.Column(db.Enum('pending', 'paid', 'failed', name='payment_status'), default='pending')
    payment_amount = db.Column(Numeric(10, 2))
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(255))
    
    # Document paths (simulated for prototype)
    passport_photo_path = db.Column(db.String(255))
    student_id_card_path = db.Column(db.String(255))
    
    # Status and admin handling
    status = db.Column(db.Enum('pending', 'accepted', 'rejected', name='request_status'), default='pending')
    claimed_by = db.Column(db.String(255))  # Admin who claimed this request
    claimed_at = db.Column(db.DateTime)
    admin_note = db.Column(db.Text)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    selected_batch = db.relationship('Batch', backref='registration_requests')
    
    @property
    def status_badge_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            'pending': 'bg-amber-100 text-amber-800',
            'accepted': 'bg-emerald-100 text-emerald-800',
            'rejected': 'bg-rose-100 text-rose-800'
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')
    
    @property
    def payment_badge_class(self):
        """Return CSS class for payment status badge"""
        payment_classes = {
            'paid': 'bg-emerald-100 text-emerald-800',
            'pending': 'bg-amber-100 text-amber-800',
            'failed': 'bg-rose-100 text-rose-800'
        }
        return payment_classes.get(self.payment_status, 'bg-gray-100 text-gray-800')
    
    @property
    def formatted_submitted_date(self):
        """Return formatted submission date"""
        if self.submitted_at:
            return self.submitted_at.strftime('%Y-%m-%d %H:%M')
        return 'N/A'