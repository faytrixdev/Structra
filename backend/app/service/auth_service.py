from uuid import UUID
import bcrypt
from jose import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.models import User, Organization, OrganizationMember
from app.domain.types import MemberRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password[:72].encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain[:72].encode(), hashed.encode())


def create_token(user_id: UUID, organization_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def register_user(db: Session, email: str, password: str, name: str, organization_name: str) -> dict:
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Email already registered")
    org = Organization(name=organization_name, slug=organization_name.lower().replace(" ", "-"))
    db.add(org)
    db.flush()
    user = User(email=email, name=name, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    member = OrganizationMember(user_id=user.id, organization_id=org.id, role=MemberRole.OWNER)
    db.add(member)
    db.commit()
    token = create_token(user.id, org.id)
    return {"token": token, "user": {"id": str(user.id), "email": user.email, "name": user.name}}


def authenticate_user(db: Session, email: str, password: str) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not member:
        raise ValueError("No organization found")
    token = create_token(user.id, member.organization_id)
    return {"token": token, "user": {"id": str(user.id), "email": user.email, "name": user.name}}
