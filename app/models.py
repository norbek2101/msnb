from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Post")
    content = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Optional: You can add lazy="selectin" here too
    owner = relationship("User", back_populates="posts", lazy="selectin") 

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    
    # <--- THE FIX: lazy="selectin"
    posts = relationship("Post", back_populates="owner", lazy="selectin")