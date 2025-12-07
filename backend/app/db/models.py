from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Query(Base):
    """Store user queries for stock research"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(50), nullable=False)  # Format: YYYY-MM-DD
    time = Column(String(50), nullable=False)  # Format: HH:MM:SS
    request = Column(Text, nullable=False)  # User's original request
    company = Column(String(255), nullable=False, index=True)  # Company name/ticker
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    reports = relationship("Report", back_populates="query", cascade="all, delete-orphan")


class Report(Base):
    """Store generated reports"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    company = Column(String(255), nullable=False, index=True)
    report_path = Column(String(500), nullable=False)  # Path to PDF file
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)  # Version number for same company
    
    # Relationships
    query = relationship("Query", back_populates="reports")
    report_data = relationship("ReportData", back_populates="report", uselist=False, cascade="all, delete-orphan")


class ReportData(Base):
    """Store raw agent outputs for each report"""
    __tablename__ = "report_data"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, unique=True)
    company_info = Column(Text, nullable=True)  # JSON string from company agent
    financial_data = Column(Text, nullable=True)  # JSON string from financial agent
    risk_data = Column(Text, nullable=True)  # JSON string from risk agent
    news_data = Column(Text, nullable=True)  # JSON string from news agent
    
    # Relationships
    report = relationship("Report", back_populates="report_data")

