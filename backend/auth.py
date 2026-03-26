"""用户认证：注册、登录、JWT Token"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

from models import User, get_db

SECRET_KEY = "videosnap-secret-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def make_token(user_id: str) -> str:
    exp = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
                     db: Session = Depends(get_db)) -> Optional[User]:
    if not creds:
        return None
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    except JWTError:
        return None


def get_user_plan(user: Optional[User]) -> str:
    """获取用户当前有效套餐"""
    if not user:
        return "free"
    if user.plan in ("pro", "annual"):
        # 检查是否过期
        if user.sub_expires and user.sub_expires < datetime.utcnow():
            return "free"
        return user.plan
    return "free"


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="邮箱已注册")
    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_pw=pwd_ctx.hash(body.password),
    )
    db.add(user)
    db.commit()
    return {"token": make_token(user.id), "plan": "free", "email": user.email}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not pwd_ctx.verify(body.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    from auth import get_user_plan
    return {"token": make_token(user.id), "plan": get_user_plan(user), "email": user.email}


@router.get("/me")
def me(user: Optional[User] = Depends(get_current_user)):
    if not user:
        return {"plan": "free", "email": None, "logged_in": False}
    from auth import get_user_plan
    return {
        "plan": get_user_plan(user),
        "email": user.email,
        "logged_in": True,
        "sub_expires": user.sub_expires.isoformat() if user.sub_expires else None,
    }
