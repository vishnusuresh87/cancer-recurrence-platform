from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.database import get_db
from app.models.user import User, UserRole
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token, verify_token
from jose import JWTError

router = APIRouter()
security = HTTPBearer()


# ==================== Schemas ====================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: dict


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    created_at: str


# ==================== Dependencies ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT
    """
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id"
            )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


# ==================== Endpoints ====================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user
    
    Steps:
    1. Check if email already exists
    2. Hash password
    3. Create user in database
    4. Issue JWT token
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user
    new_user = User(
        email=request.email,
        password_hash=password_hash,
        role=UserRole.PATIENT
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create JWT
    access_token = create_access_token(data={
        "user_id": str(new_user.user_id),
        "email": new_user.email,
        "role": new_user.role.value
    })
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=15 * 60,  # 15 minutes in seconds
        user={
            "user_id": str(new_user.user_id),
            "email": new_user.email,
            "role": new_user.role.value,
            "created_at": new_user.created_at.isoformat()
        }
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login existing user
    
    Steps:
    1. Find user by email
    2. Verify password
    3. Update last_login
    4. Issue JWT token
    """
    # Find user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create JWT
    access_token = create_access_token(data={
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role.value
    })
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=15 * 60,
        user={
            "user_id": str(user.user_id),
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat()
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile
    Requires: Valid JWT in Authorization header
    """
    return UserResponse(
        user_id=str(current_user.user_id),
        email=current_user.email,
        role=current_user.role.value,
        created_at=current_user.created_at.isoformat()
    )


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-service"}


    