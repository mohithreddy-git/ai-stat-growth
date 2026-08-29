from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models import Department, Role, User


def authenticate_user(db: Session, email: str, password: str) -> tuple[str, User] | None:
    user = db.scalar(select(User).where(User.email == email.lower(), User.is_active.is_(True)))
    if user is None or not verify_password(password, user.password_hash):
        return None
    role = db.get(Role, user.role_id)
    if role is None:
        return None
    return create_access_token(user.employee_id, role.name), user


def user_to_summary(db: Session, user: User) -> dict:
    role = db.get(Role, user.role_id)
    department = db.get(Department, user.department_id)
    return {
        "id": user.id,
        "employee_id": user.employee_id,
        "email": user.email,
        "full_name": user.full_name,
        "designation": user.designation,
        "division": user.division,
        "current_assignment": user.current_assignment,
        "years_experience": user.years_experience,
        "domain": user.domain,
        "current_role": user.current_role,
        "career_goal": user.career_goal,
        "role": role.name if role else "UNKNOWN",
        "department": department.name if department else "Unknown department",
        "is_demo": user.is_demo,
    }
