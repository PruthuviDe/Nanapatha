# Sample Data for NanaPatha Educational Institute
# Run this script to populate sample registration requests

from app import app, db
from models import RegistrationRequest, Batch, User, StudentProfile
from datetime import datetime, date
from werkzeug.security import generate_password_hash
import random

def seed_sample_data():
    """Add sample registration requests to demonstrate the workflow"""
    
    with app.app_context():
        # Clear existing registration requests
        RegistrationRequest.query.delete()
        
        # Sample existing students (these are students already in institute but need LMS accounts)
        existing_students = [
            {
                'name': 'Aarav Patel',
                'email': 'aarav.patel@email.com',
                'mobile': '+94701234567',
                'student_id_number': 'NP2024001',
                'registration_type': 'existing',
                'payment_status': 'paid',  # Already paid to institute
                'status': 'pending',
                'submitted_at': datetime.utcnow(),
                'address': '123 Colombo Road, Kandy',
                'dob': date(2008, 5, 15),
                'grade': 'Grade 10',
                'class_type': 'physical'
            },
            {
                'name': 'Ishara Fernando',
                'email': 'ishara.fernando@email.com', 
                'mobile': '+94712345678',
                'student_id_number': 'NP2024002',
                'registration_type': 'existing',
                'payment_status': 'paid',
                'status': 'pending',
                'submitted_at': datetime.utcnow(),
                'address': '456 Galle Road, Colombo',
                'dob': date(2007, 8, 22),
                'grade': 'Grade 11',
                'class_type': 'online'
            },
            {
                'name': 'Kavindi Silva',
                'email': 'kavindi.silva@email.com',
                'mobile': '+94723456789',
                'student_id_number': 'NP2024003', 
                'registration_type': 'existing',
                'payment_status': 'paid',
                'status': 'pending',
                'submitted_at': datetime.utcnow(),
                'address': '789 Main Street, Matara',
                'dob': date(2008, 12, 10),
                'grade': 'Grade 10',
                'class_type': 'both'
            }
        ]
        
        # Sample new students (completely new to the institute)
        new_students = [
            {
                'name': 'Dhanush Rajapaksa',
                'email': 'dhanush.rajapaksa@email.com',
                'mobile': '+94734567890',
                'registration_type': 'new',
                'payment_status': 'pending',
                'status': 'pending', 
                'submitted_at': datetime.utcnow(),
                'address': '321 Temple Road, Negombo',
                'dob': date(2009, 3, 18),
                'grade': 'Grade 9',
                'class_type': 'physical',
                'selected_batch_id': 1  # Assuming batch ID 1 exists
            },
            {
                'name': 'Sachini Perera',
                'email': 'sachini.perera@email.com',
                'mobile': '+94745678901',
                'registration_type': 'new', 
                'payment_status': 'pending',
                'status': 'pending',
                'submitted_at': datetime.utcnow(),
                'address': '654 Beach Road, Galle',
                'dob': date(2008, 7, 25),
                'grade': 'Grade 10',
                'class_type': 'online',
                'selected_batch_id': 2
            },
            {
                'name': 'Nimesh Wickramasinghe',
                'email': 'nimesh.wickramasinghe@email.com',
                'mobile': '+94756789012',
                'registration_type': 'new',
                'payment_status': 'paid',  # Some new students may have pre-paid
                'status': 'pending',
                'submitted_at': datetime.utcnow(), 
                'address': '987 Hill Street, Kandy',
                'dob': date(2007, 11, 8),
                'grade': 'Grade 11',
                'class_type': 'both',
                'selected_batch_id': 1
            }
        ]
        
        # Add existing student registrations
        for student_data in existing_students:
            registration = RegistrationRequest(**student_data)
            db.session.add(registration)
            
        # Add new student registrations  
        for student_data in new_students:
            registration = RegistrationRequest(**student_data)
            db.session.add(registration)
            
        # Add one accepted existing student example
        accepted_existing = RegistrationRequest(
            name='Tharindu Jayawardena',
            email='tharindu.jayawardena@email.com',
            mobile='+94767890123',
            student_id_number='NP2024004',
            registration_type='existing',
            payment_status='paid',
            status='accepted',
            submitted_at=datetime.utcnow(),
            address='147 Lake Road, Colombo',
            dob=date(2008, 4, 12),
            grade='Grade 10',
            class_type='physical',
            admin_note='Verified student ID and created LMS account. Enrolled in current classes as per physical forms.'
        )
        db.session.add(accepted_existing)
        
        # Add one rejected example
        rejected_registration = RegistrationRequest(
            name='Invalid Student',
            email='invalid@email.com',
            mobile='+94778901234',
            student_id_number='INVALID001',
            registration_type='existing',
            payment_status='paid',
            status='rejected',
            submitted_at=datetime.utcnow(),
            admin_note='Student ID could not be verified in institute records.'
        )
        db.session.add(rejected_registration)
            
        db.session.commit()
        print("✅ Sample registration data added successfully!")
        print("\n📋 Summary:")
        print(f"   • {len(existing_students)} Existing Student Registrations")
        print(f"   • {len(new_students)} New Student Registrations") 
        print(f"   • 1 Accepted Registration Example")
        print(f"   • 1 Rejected Registration Example")
        print(f"   • Total: {len(existing_students) + len(new_students) + 2} Registration Requests")
        
        print("\n🔍 Admin Workflow:")
        print("   1. Existing Students: Verify Student ID → Check Institute Records → Create LMS Account → Enroll in Current Classes")
        print("   2. New Students: Review Application → Process Payment → Create Student Record → Create LMS Account → Enroll in Selected Batch")

if __name__ == '__main__':
    seed_sample_data()