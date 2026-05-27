"""Smoke tests for repository helpers via an in-memory SQLite engine.
pgvector-specific helpers are exercised via unit tests with mocked sessions
because SQLite doesn't speak the vector type."""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.db.repositories import portfolio as portfolio_repo
from app.db.repositories import queries as queries_repo
from app.db.repositories import reports as reports_repo


# --- Minimal SQLite-compatible mirror of the models (drops the Vector column) ---

class Base(DeclarativeBase):
    pass


class _Query(Base):
    __tablename__ = "queries"
    id = Column(String, primary_key=True)
    request = Column(Text, nullable=False)
    company = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class _Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True)
    query_id = Column(String, ForeignKey("queries.id"), nullable=False)
    company = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    report_path = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())


class _ReportData(Base):
    __tablename__ = "report_data"
    report_id = Column(String, ForeignKey("reports.id", ondelete="CASCADE"), primary_key=True)
    company_info = Column(Text, nullable=True)
    financial_data = Column(Text, nullable=True)
    risk_data = Column(Text, nullable=True)
    news_data = Column(Text, nullable=True)
    analysis = Column(Text, nullable=True)


class _Portfolio(Base):
    __tablename__ = "portfolio"
    ticker = Column(String, primary_key=True)
    shares = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=True)
    company_name = Column(String, nullable=True)
    holding_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


@pytest_asyncio.fixture()
async def session(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Patch the model imports inside each repo to point at the SQLite mirrors
    from app.db.repositories import queries as q_mod
    from app.db.repositories import reports as r_mod
    from app.db.repositories import portfolio as p_mod
    monkeypatch.setattr(q_mod, "Query", _Query)
    monkeypatch.setattr(r_mod, "Report", _Report)
    monkeypatch.setattr(r_mod, "ReportData", _ReportData)
    monkeypatch.setattr(p_mod, "PortfolioHolding", _Portfolio)

    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_query_create_and_round_trip(session):
    row = await queries_repo.create_query(
        session, request="test", company="Apple (AAPL)", ticker="aapl"
    )
    await session.commit()
    assert row["ticker"] == "AAPL"
    assert row["company"] == "Apple (AAPL)"


@pytest.mark.asyncio
async def test_report_version_increments_per_ticker(session):
    q = await queries_repo.create_query(session, request="r", company="Apple (AAPL)", ticker="AAPL")
    r1 = await reports_repo.create_report(
        session, query_id=q["id"], company="Apple (AAPL)", ticker="AAPL", report_path="/r/1.pdf"
    )
    r2 = await reports_repo.create_report(
        session, query_id=q["id"], company="Apple (AAPL)", ticker="AAPL", report_path="/r/2.pdf"
    )
    await session.commit()
    assert r1["version"] == 1
    assert r2["version"] == 2


@pytest.mark.asyncio
async def test_portfolio_insert_update_delete(session):
    inserted = await portfolio_repo.insert(
        session, ticker="aapl", shares=10, company_name="Apple", holding_id="h1"
    )
    await session.commit()
    assert inserted["ticker"] == "AAPL"
    assert inserted["shares"] == 10

    updated = await portfolio_repo.update_shares(session, ticker="AAPL", shares=25)
    await session.commit()
    assert updated["shares"] == 25

    ok = await portfolio_repo.delete(session, "aapl")
    await session.commit()
    assert ok is True
    assert await portfolio_repo.get(session, "AAPL") is None
