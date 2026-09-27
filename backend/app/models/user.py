import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.FREE, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    credit_balance: Mapped["CreditBalance"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    video_jobs: Mapped[List["VideoJob"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    # SavedChart İlişkisi Entegrasyonu
    charts: Mapped[List["SavedChart"]] = relationship("SavedChart", back_populates="owner", cascade="all, delete-orphan")

    @property
    def is_premium(self) -> bool:
        return self.role in (UserRole.PREMIUM, UserRole.ADMIN)


class SavedChart(Base):
    __tablename__ = "saved_charts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Doğum Haritası")

    # Doğum Verileri
    year: Mapped[int] = mapped_column(Integer, nullable=False, default=1987)
    month: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    day: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    hour: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    minute: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lat: Mapped[float] = mapped_column(Float, nullable=False, default=41.0082)
    lon: Mapped[float] = mapped_column(Float, nullable=False, default=28.9784)
    timezone_str: Mapped[str] = mapped_column(String(100), default="Europe/Istanbul")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # User İlişkisi
    owner: Mapped["User"] = relationship("User", back_populates="charts")