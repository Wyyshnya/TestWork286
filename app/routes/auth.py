from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..dependencies import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserLogin
from ..services.auth_service import get_password_hash, create_access_token, create_refresh_token, verify_token
from ..services.auth_service import verify_password
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Authentication"], prefix="/auth")

@router.post(
    "/register",
    summary="Регистрация нового пользователя",
    description="Создаёт нового пользователя с указанным именем, email и паролем. Пароль хешируется перед сохранением в базу данных.",
    responses={
        200: {
            "description": "Пользователь успешно зарегистрирован",
            "content": {
                "application/json": {
                    "example": {
                        "msg": "User registered"
                    }
                }
            }
        },
        422: {
            "description": "Некорректные входные данные (например, неверный формат email или слабый пароль)"
        }
    }
)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"msg": "User registered"}

@router.post(
    "/login",
    summary="Вход в систему",
    description="Аутентифицирует пользователя по email и паролю, возвращая JWT access token и refresh token.",
    responses={
        200: {
            "description": "Успешная аутентификация",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Неверный email или пароль",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect email or password"
                    }
                }
            }
        },
        422: {
            "description": "Некорректные входные данные"
        }
    }
)
async def login(form_data: UserLogin = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.execute(select(User).filter(User.email == form_data.email))
    user = user.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post(
    "/refresh",
    summary="Обновление access token",
    description="Обновляет access token, используя действительный refresh token. Возвращает новый access token.",
    responses={
        200: {
            "description": "Access token успешно обновлён",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Недействительный refresh token или пользователь не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid refresh token"
                    }
                }
            }
        },
        422: {
            "description": "Некорректный формат refresh token"
        }
    }
)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = verify_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = await db.execute(select(User).filter(User.email == payload.get("sub")))
    user = user.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}