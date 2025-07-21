from app import create_app
from app.extensions import db
from app.models import Role

app = create_app()

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
    db.session.commit()
    print("Roles seeded.")