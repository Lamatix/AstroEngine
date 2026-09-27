from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead, summary="Mevcut Kullanıcı Profil Bilgileri")
async def get_me(user: User = Depends(get_current_active_user)):
    """
    Oturum açmış ve aktif olan kullanıcının profil bilgilerini (kredi bakiyesi, email, isim vb.) döndürür.
    """
    return user