from app import create_app, db
from models import User
import bcrypt

app = create_app()

with app.app_context():
    users = User.query.all()
    for user in users:
        # Assuming you know the original password or using a default password
        original_password = "default_password"  # Replace with actual password if known
        user.set_password(original_password)
    db.session.commit()

print("All user passwords have been updated.")
