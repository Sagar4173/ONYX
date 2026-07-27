
from fastapi import HTTPException

from database import db_manager


async def get_database():
    if db_manager.db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return db_manager.db
