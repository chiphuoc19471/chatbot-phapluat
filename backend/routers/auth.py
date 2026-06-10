from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
from models.user import User
from auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Pydantic Schemas ---

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class RegisterResponse(BaseModel):
    message: str
    user_id: int

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserInfo(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


# --- Endpoints ---

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_200_OK)
def register(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new user.
    Checks if email already exists, hashes the password, and saves the user.
    """
    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng"
        )
    
    # Hash password and create User
    hashed_pw = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        name=user_data.name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RegisterResponse(message="Đăng ký thành công", user_id=new_user.id)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates a user and returns a JWT token.
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng"
        )
    
    # Create Access Token
    access_token = create_access_token(data={"sub": user.email})
    
    # Map to schema response
    user_info = UserInfo.model_validate(user)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_info
    )
