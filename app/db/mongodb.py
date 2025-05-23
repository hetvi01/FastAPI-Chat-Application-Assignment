import ssl
import motor.motor_asyncio
from app.core.config import settings


client = motor.motor_asyncio.AsyncIOMotorClient(
    settings.MONGODB_URL,
)
db = client[settings.MONGODB_DB]

# Collections
chat_content = db.chat_content


async def init_mongodb():
    # Create indexes if needed
    await chat_content.create_index("chat_id")
    await chat_content.create_index([("qa_pairs.response_id", 1)])


async def get_mongodb():
    return db 