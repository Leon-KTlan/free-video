"""数据库模型：用户、订阅、下载记录"""
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

DB_PATH = Path(__file__).parent / "videosnap.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id          = Column(String, primary_key=True)   # UUID
    email       = Column(String, unique=True, index=True)
    hashed_pw   = Column(String)
    plan        = Column(String, default="free")     # free / pro / annual
    sub_expires = Column(DateTime, nullable=True)    # 订阅到期时间
    stripe_customer_id = Column(String, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    is_active   = Column(Boolean, default=True)


class DownloadLog(Base):
    __tablename__ = "download_logs"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String, index=True)          # 匿名用户用 IP
    url        = Column(String)
    quality    = Column(Integer, default=0)          # 实际下载画质高度
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
