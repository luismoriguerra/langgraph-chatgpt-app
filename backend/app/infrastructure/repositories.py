from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities import Conversation, Message
from app.infrastructure.models import ConversationModel, MessageModel


class SqlAlchemyConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, conversation: Conversation) -> Conversation:
        model = ConversationModel(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, id: UUID) -> Conversation | None:
        result = await self._session.get(ConversationModel, id)
        return self._to_entity(result) if result else None

    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[Conversation]:
        stmt = (
            select(ConversationModel)
            .order_by(ConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def count(self) -> int:
        stmt = select(func.count()).select_from(ConversationModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update_title(self, id: UUID, title: str) -> None:
        stmt = update(ConversationModel).where(ConversationModel.id == id).values(title=title)
        await self._session.execute(stmt)
        await self._session.commit()

    async def update_timestamp(self, id: UUID) -> None:
        stmt = (
            update(ConversationModel)
            .where(ConversationModel.id == id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def delete(self, id: UUID) -> None:
        stmt = delete(ConversationModel).where(ConversationModel.id == id)
        await self._session.execute(stmt)
        await self._session.commit()

    @staticmethod
    def _to_entity(model: ConversationModel) -> Conversation:
        return Conversation(
            id=model.id,
            title=model.title,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, message: Message) -> Message:
        model = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def list_by_conversation(self, conversation_id: UUID) -> list[Message]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    @staticmethod
    def _to_entity(model: MessageModel) -> Message:
        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            role=model.role,
            content=model.content,
            created_at=model.created_at,
        )
