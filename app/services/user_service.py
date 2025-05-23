from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User


class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db_session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db_session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db_session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def authenticate(self, email: str = None, password: str = None) -> Optional[User]:
        if email:
            user = await self.get_by_email(email=email)
        else:
            return None
            
        if not user:
            return ModuleNotFoundError
            
        if not verify_password(password, user.hashed_password):
            return None
            
        return user

    async def create_user(self, email: str, username: str, password: str) -> User:
        # Check if user with the same email exists
        db_user = await self.get_by_email(email=email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Check if user with the same username exists
        db_user = await self.get_by_username(username=username)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
            
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password)
        )
            
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
            
        return user 