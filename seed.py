from app import app
from models import db, User, StudentProfile, TeacherProfile, Batch, RegistrationRequest, Classroom, ClassSession
from datetime import datetime, date
import os

def create_sample_data():
    """Create sample data for testing the admin dashboard"""
    
    # Ensure data directory exists BEFORE app context
    os.makedirs('data', exist_ok=True)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        print("Creating sample batches...")
        # Create sample batches
        batches = [
            Batch(
                name="A/L Physics 2026 - Batch A",
                grade="A/L",
                subject="Physics",
                capacity=30,
                teacher_name="Mr. Kamal Perera",
                class_type="physical",
                notes="Advanced level physics for 2026 exam"
            ),
            Batch(
                name="A/L Chemistry 2026 - Online",
                grade="A/L", 
                subject="Chemistry",
                capacity=25,
                teacher_name="Dr. Nimal Silva",
                class_type="online",
                notes="Online chemistry classes with lab simulations"
            ),
            Batch(
                name="O/L Mathematics - Basic",
                grade="O/L",
                subject="Mathematics", 
                capacity=35,
                teacher_name="Ms. Priya Fernando",
                class_type="both",
                notes="Ordinary level mathematics foundation"
            ),
            Batch(
                name="A/L Biology 2026 - Intensive",
                grade="A/L",
                subject="Biology",
                capacity=20,
                teacher_name="Dr. Samantha Raj",
                class_type="physical", 
                notes="Intensive biology course with practical sessions"
            )
        ]
        
        for batch in batches:
            db.session.add(batch)
        
        db.session.commit()
        print(f"Created {len(batches)} sample batches")
        
        print("Creating sample registration requests...")
        # Create sample registration requests
        requests = [
            RegistrationRequest(
                name="Ashan Jayasinghe", 
                email="ashan.jayasinghe@email.com",
                mobile="0771234567",
                address="123 Galle Road, Colombo 03",
                dob=date(2005, 5, 15),
                grade="A/L",
                class_type="physical",
                selected_batch_id=1,  # A/L Physics
                registration_type="new",
                payment_status="pending",
                payment_amount=15000,
                payment_method="online_payment",
                status="pending",
                submitted_at=datetime(2024, 10, 1, 14, 30)
            ),
            RegistrationRequest(
                name="Kavindi Perera",
                email="kavindi.perera@email.com", 
                mobile="0777654321",
                address="456 Kandy Road, Kurunegala",
                dob=date(2006, 8, 22),
                grade="A/L",
                class_type="online",
                selected_batch_id=2,  # A/L Chemistry Online
                registration_type="new",
                payment_status="paid",
                payment_amount=15000,
                payment_method="bank_transfer",
                status="pending",
                submitted_at=datetime(2024, 10, 5, 9, 15)
            ),
            RegistrationRequest(
                name="Nipun Fernando",
                email="nipun.fernando@email.com",
                mobile="0712345678", 
                student_id_number="NP2023045",
                registration_type="existing",
                payment_status="paid",
                status="pending",
                submitted_at=datetime(2024, 10, 8, 16, 45)
            ),
            RegistrationRequest(
                name="Sachini Silva",
                email="sachini.silva@email.com",
                mobile="0765432189",
                address="789 Matara Road, Galle", 
                dob=date(2007, 3, 10),
                grade="O/L",
                class_type="both",
                selected_batch_id=3,  # O/L Mathematics
                registration_type="new",
                payment_status="pending",
                payment_amount=12000,
                payment_method="cash",
                status="pending", 
                claimed_by="Admin User",
                claimed_at=datetime(2024, 10, 9, 10, 30),
                submitted_at=datetime(2024, 10, 7, 11, 20)
            ),
            RegistrationRequest(
                name="Ruwan Bandara",
                email="ruwan.bandara@email.com",
                mobile="0778899001",
                address="321 Negombo Road, Ja-Ela",
                dob=date(2005, 12, 5),
                grade="A/L",
                class_type="physical", 
                selected_batch_id=4,  # A/L Biology
                registration_type="new",
                payment_status="paid",
                payment_amount=15000,
                payment_method="card_payment",
                status="accepted",
                admin_note="Accepted by admin on 2024-10-09 14:30. Student account created successfully.",
                submitted_at=datetime(2024, 10, 2, 13, 45),
                processed_at=datetime(2024, 10, 9, 14, 30)
            ),
            RegistrationRequest(
                name="Malsha Wijesinghe", 
                email="malsha.wijesinghe@email.com",
                mobile="0701234567",
                student_id_number="NP2022078",
                registration_type="existing",
                payment_status="paid",
                status="rejected",
                admin_note="Student ID not found in institute records. Please contact support with proper documentation.",
                submitted_at=datetime(2024, 9, 28, 8, 15),
                processed_at=datetime(2024, 10, 3, 12, 00)
            )
        ]
        
        for request in requests:
            db.session.add(request)
        
        db.session.commit()
        print(f"Created {len(requests)} sample registration requests")
        
        print("Creating sample admin user...")
        # Create a sample admin user
        admin_user = User(
            name="Admin User",
            email="admin@nanapatha.com",
            role="admin",
            status="active",
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        
        print("Creating sample classrooms...")
        # Create sample classrooms
        classrooms = [
            Classroom(
                name="Room A-101",
                capacity=35,
                location="Main Building, 1st Floor",
                notes="Equipped with projector and whiteboard"
            ),
            Classroom(
                name="Lab B-201", 
                capacity=25,
                location="Science Block, 2nd Floor",
                notes="Chemistry laboratory with fume hoods"
            ),
            Classroom(
                name="Room C-305",
                capacity=40,
                location="New Building, 3rd Floor", 
                notes="Large classroom for mathematics classes"
            )
        ]
        
        for classroom in classrooms:
            db.session.add(classroom)
        
        db.session.commit()
        print(f"Created {len(classrooms)} sample classrooms")
        
        print("\nSample data created successfully!")
        print("=" * 50)
        print("SUMMARY:")
        print(f"- {len(batches)} Batches created")
        print(f"- {len(requests)} Registration requests created")
        print(f"- 1 Admin user created") 
        print(f"- {len(classrooms)} Classrooms created")
        print("\nRegistration status breakdown:")
        print(f"- Pending: {len([r for r in requests if r.status == 'pending'])}")
        print(f"- Accepted: {len([r for r in requests if r.status == 'accepted'])}")
        print(f"- Rejected: {len([r for r in requests if r.status == 'rejected'])}")
        print("\nPayment status breakdown:")
        print(f"- Paid: {len([r for r in requests if r.payment_status == 'paid'])}")
        print(f"- Pending: {len([r for r in requests if r.payment_status == 'pending'])}")
        print("=" * 50)

if __name__ == '__main__':
    create_sample_data()