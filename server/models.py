from sqlalchemy import Column, Integer, String
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, nullable=False)  # Фамилия
    first_name = Column(String, nullable=False)  # Имя
    father_name = Column(String)  # Отчество (необязательно)
    email = Column(String, unique=True, index=True, nullable=False)
    university = Column(String, nullable=False)  # ВУЗ
    password = Column(String, nullable=False)  # Хеш пароля
