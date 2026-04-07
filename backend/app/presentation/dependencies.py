from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.infrastructure.database import get_db_session
from app.infrastructure.repositories import (
    SqlAlchemyConversationRepository,
    SqlAlchemyMessageRepository,
)


def get_settings() -> Settings:
    return settings


async def get_conversation_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SqlAlchemyConversationRepository:
    return SqlAlchemyConversationRepository(session)


async def get_message_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SqlAlchemyMessageRepository:
    return SqlAlchemyMessageRepository(session)
