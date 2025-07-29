from app import create_app
from app.models import User, Role, Department, UserAssignment
from app.extensions import db
from werkzeug.security import generate_password_hash

app = create_app()

def seed():
    admin = User(name="Admin", email="admin@example.com", password_hash=generate_password_hash("adminpass"))
    db.session.add(admin)

    admin_role = Role.query.filter_by(level=100).first()
    if not admin_role:
        admin_role = Role(name="Admin", level=100)
        db.session.add(admin_role)

    default_dept = Department.query.first()
    if not default_dept:
        default_dept = Department(name="Default")
        db.session.add(default_dept)

    assignment = UserAssignment(user=admin, role=admin_role, department=default_dept)
    db.session.add(assignment)

with app.app_context():
    roles = [
        ('Giám đốc TT', 100),
        ('Phó Giám đốc TT', 90),
        ('Trưởng phòng', 80),
        ('Phó phòng', 70),
        ('Tổ trưởng', 60),
        ('Tổng hợp', 85),
        ('Chuyên viên', 50),
        ('Fresher', 30),
        ('Thực tập sinh', 10),
    ]

    for name, level in roles:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, level=level))
    seed()
    db.session.commit()
    print("Roles seeded.")
    print("Super admin seeded.")