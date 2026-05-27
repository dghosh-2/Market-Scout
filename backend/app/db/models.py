"""SQLAlchemy ORM models for Market Scout (Postgres + pgvector)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid_str() -> str:
    return str(uuid.uuid4())


class User(Base):
    """Minimal user table — required so PortfolioInsight.user_id has a real FK target.
    There is no real auth in MarketScout yet; row id=0 is the default 'system' user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid_str)
    request: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    reports: Mapped[list["Report"]] = relationship(back_populates="query")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid_str)
    query_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("queries.id"), nullable=False
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    report_path: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    query: Mapped[Query] = relationship(back_populates="reports")
    data: Mapped[Optional["ReportData"]] = relationship(
        back_populates="report", uselist=False, cascade="all, delete-orphan"
    )


class ReportData(Base):
    __tablename__ = "report_data"

    report_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("reports.id", ondelete="CASCADE"),
        primary_key=True,
    )
    company_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    financial_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    risk_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    news_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    report: Mapped[Report] = relationship(back_populates="data")


class PortfolioHolding(Base):
    __tablename__ = "portfolio"

    ticker: Mapped[str] = mapped_column(String(32), primary_key=True)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    holding_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PortfolioInsight(Base):
    """Agent-generated insights stored with embeddings for fast semantic recall."""

    __tablename__ = "portfolio_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, default=0
    )
    portfolio_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    insight_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_portfolio_insights_user",
            "user_id",
        ),
        Index(
            "ix_portfolio_insights_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
