from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import logging
from . import models, schemas, crud, auth
from .database import SessionLocal, engine

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error",
        )
    finally:
        db.close()


@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Attempting to register user: {user.email}")

        db_user = crud.get_user(db, email=user.email)
        if db_user:
            logger.warning(f"Email already exists: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован",
            )

        created_user = crud.create_user(db=db, user=user)
        logger.info(f"User registered successfully: {user.email}")
        return created_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регистрации пользователя",
        )


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    try:
        logger.info(f"Login attempt for: {user.email}")

        db_user = crud.get_user(db, email=user.email)
        if not db_user or not auth.verify_password(user.password, db_user.password):
            logger.warning(f"Invalid login attempt for: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный email или пароль",
            )

        access_token = auth.create_access_token(data={"sub": db_user.email})
        logger.info(f"Successful login for: {user.email}")
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        logger.error(f"Login error for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при входе в систему",
        )


@app.get("/account")
def get_account(
    token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невалидный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        logger.info("Account access attempt")

        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            logger.warning("Invalid token: missing email")
            raise credentials_exception

        user = crud.get_user(db, email=email)
        if user is None:
            logger.warning(f"User not found for token: {email}")
            raise credentials_exception

        logger.info(f"Successful account access for: {email}")
        return {
            "last_name": user.last_name,
            "first_name": user.first_name,
            "father_name": user.father_name,
            "university": user.university,
        }

    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Account access error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении данных пользователя",
        )
