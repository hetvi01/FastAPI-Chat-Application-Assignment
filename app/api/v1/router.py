from fastapi import APIRouter

from app.api.v1.endpoints import auth, chats, messages, branches

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(branches.router, prefix="/branches", tags=["branches"]) 