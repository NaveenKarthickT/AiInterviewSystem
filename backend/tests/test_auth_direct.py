import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.api.v1.auth import register, login, get_current_user
from app.core.security import verify_password, decode_access_token

# Initialize tables
Base.metadata.create_all(bind=engine)


def test_auth_pipeline():
    db = SessionLocal()
    test_email = "direct_candidate@test.com"
    test_password = "ComplexPassword99!"
    test_name = "Jordan Candidate"

    try:
        # Clean up any previous test user
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        # 1. Test Registration
        user_in = UserCreate(
            email=test_email,
            password=test_password,
            full_name=test_name
        )
        token_response = register(user_in=user_in, db=db)
        print("[SUCCESS] Registration completed.")
        assert token_response.access_token is not None
        assert token_response.user.email == test_email
        assert token_response.user.full_name == test_name
        print(f"[SUCCESS] User registered with ID: {token_response.user.id}")

        # 2. Test Password Hashing
        db_user = db.query(User).filter(User.email == test_email).first()
        assert db_user is not None
        assert db_user.hashed_password != test_password
        assert verify_password(test_password, db_user.hashed_password) is True
        assert verify_password("WrongPassword!", db_user.hashed_password) is False
        print("[SUCCESS] Password hashing and verification verified.")

        # 3. Test Login
        login_in = UserLogin(email=test_email, password=test_password)
        login_token = login(login_data=login_in, db=db)
        assert login_token.access_token is not None
        assert login_token.user.email == test_email
        print("[SUCCESS] Login authentication successful.")

        # 4. Test Token Decoding & get_current_user dependency
        payload = decode_access_token(login_token.access_token)
        assert payload is not None
        assert payload["sub"] == str(db_user.id)
        current_user = get_current_user(db=db, token=login_token.access_token)
        assert current_user.id == db_user.id
        assert current_user.email == test_email
        print("[SUCCESS] Token decoding and get_current_user passed.")

        print("\n=== ALL AUTHENTICATION & DATABASE TESTS PASSED! ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_auth_pipeline()
