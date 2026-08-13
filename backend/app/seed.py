import logging
from app.core.db import SessionLocal, engine, Base
import app.models
from app.models.user import User
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_admin():
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        admin_email = "admin@seo.com"
        admin_password = "admin@123"
        
        user = db.query(User).filter(User.email == admin_email).first()
        hashed_password = get_password_hash(admin_password)
        
        if user:
            logger.info(f"Updating existing admin user: {admin_email}")
            user.password_hash = hashed_password
            user.plan = "agency"
        else:
            logger.info(f"Creating new admin user: {admin_email}")
            user = User(
                email=admin_email,
                password_hash=hashed_password,
                plan="agency"
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        logger.info(f"Successfully seeded admin user ID: {user.id}, Email: {user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding admin user: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
