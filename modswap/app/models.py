from datetime import datetime
from typing import Optional
from flask_login import UserMixin
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .extensions import db


user_modules = Table(
    "user_modules",
    db.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("module_id", ForeignKey("modules.id"), primary_key=True),
)


swap_give_modules = Table(
    "swap_give_modules",
    db.metadata,
    Column("swap_id", ForeignKey("swap_requests.id"), primary_key=True),
    Column("module_id", ForeignKey("modules.id"), primary_key=True),
)


swap_want_modules = Table(
    "swap_want_modules",
    db.metadata,
    Column("swap_id", ForeignKey("swap_requests.id"), primary_key=True),
    Column("module_id", ForeignKey("modules.id"), primary_key=True),
)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    university: Mapped[str] = mapped_column(String(255), nullable=True)
    degree: Mapped[str] = mapped_column(String(255), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="student")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modules = relationship("Module", secondary=user_modules, back_populates="students")


class Module(db.Model):
    __tablename__ = "modules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=True)
    university: Mapped[str] = mapped_column(String(255), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    students = relationship("User", secondary=user_modules, back_populates="modules")


class SwapRequest(db.Model):
    __tablename__ = "swap_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User")
    giving = relationship("Module", secondary=swap_give_modules)
    wanting = relationship("Module", secondary=swap_want_modules)


class Message(db.Model):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    swap_id: Mapped[int] = mapped_column(ForeignKey("swap_requests.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)