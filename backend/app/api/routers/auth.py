import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import RefreshRequest, TokenPair, UserCreate, UserLogin, UserRead
from app.services.credit_service import grant_signup_bonus

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ------------------------------------------------------------------
# CURRENT USER DEPENDENCY
# ------------------------------------------------------------------

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """JWT Token üzerinden mevcut oturum açmış kullanıcıyı doğrular ve döndürür."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz yetkilendirme bilgileri",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı veya hesabı pasif durumunda",
        )
    return user


# ------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Yeni Kullanıcı Kaydı")
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name or "Sercan Bilir"
    )
    db.add(user)
    await db.flush()

    # Kayıt bonus kredisi tanımlama
    await grant_signup_bonus(db, user, settings.SIGNUP_BONUS_CREDITS)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair, summary="Kullanıcı Girişi ve Token Çifti Alımı")
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    # email veya username hangisi gönderildiyse onu yakalayalım
    identifier = payload.email or payload.username

    if not identifier or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="E-posta/Kullanıcı adı ve şifre gereklidir",
        )

    # Hem e-posta hem de ad alanında arama yapabilmesi için or_ koşulu
    result = await db.execute(
        select(User).where(or_(User.email == identifier, User.full_name == identifier))
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return TokenPair(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair, summary="Token Yenileme")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise ValueError("Not a refresh token")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    result = await db.execute(select(User).where(User.id == uuid.UUID(decoded["sub"])))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return TokenPair(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserRead, summary="Mevcut Kullanıcı Profil Bilgileri")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Oturum açmış olan kullanıcının profilini, güncel kredi sayısını ve bilgilerini döner."""
    return current_user