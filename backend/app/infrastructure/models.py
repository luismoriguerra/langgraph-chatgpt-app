import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False, default="New conversation...")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["MessageModel"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at",
    )

    __table_args__ = (Index("ix_conversation_updated_at", "updated_at", postgresql_using="btree"),)


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    conversation: Mapped["ConversationModel"] = relationship(back_populates="messages")
    tool_invocations: Mapped[list["ToolInvocationModel"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="ToolInvocationModel.created_at",
    )

    __table_args__ = (
        Index(
            "ix_message_conversation_created",
            "conversation_id",
            "created_at",
            postgresql_using="btree",
        ),
    )


class ToolInvocationModel(Base):
    __tablename__ = "tool_invocations"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(50), nullable=False)
    tool_input: Mapped[str] = mapped_column(Text, nullable=False)
    tool_output: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    message: Mapped["MessageModel"] = relationship(back_populates="tool_invocations")

    __table_args__ = (
        Index("ix_tool_invocation_message_id", "message_id", postgresql_using="btree"),
    )
