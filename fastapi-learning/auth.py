from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext

from database import users_collection
from schemas import UserCreate, TokenResponse, TokenRefreshRequest

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

auth_router = APIRouter()


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    refresh_payload = data.copy()
    refresh_payload.update({"type": "refresh"})
    return create_access_token(refresh_payload, expires_minutes=REFRESH_TOKEN_EXPIRE_MINUTES)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("user_id")
        role = payload.get("role", "user")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "role": role}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_roles(*allowed_roles):
    def role_checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker


@auth_router.post("/signup")
def signup(user: UserCreate):
    existing = users_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = hash_password(user.password)
    result = users_collection.insert_one({"username": user.username, "password": hashed_password, "role": "user"})
    return {"user_id": str(result.inserted_id)}


@auth_router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    role = user.get("role", "user")
    access_token = create_access_token({"user_id": str(user["_id"]), "role": role})
    refresh_token = create_refresh_token({"user_id": str(user["_id"]), "role": role})
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@auth_router.post("/token/refresh", response_model=TokenResponse)
def refresh_tokens(payload: TokenRefreshRequest):
    try:
        decoded = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = decoded.get("user_id")
        role = decoded.get("role", "user")
        access_token = create_access_token({"user_id": user_id, "role": role})
        refresh_token = create_refresh_token({"user_id": user_id, "role": role})
        return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
