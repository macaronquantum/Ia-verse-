from __future__ import annotations

from sqlalchemy import JSON, Column, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class AgentRecord(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)


class CompanyRecord(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)


class BankRecord(Base):
    __tablename__ = "banks"
    id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)


class WalletRecord(Base):
    __tablename__ = "wallets"
    id = Column(String, primary_key=True)
    owner_id = Column(String, nullable=False)
    chain = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
    encrypted_private_key = Column(String, nullable=False)


class TransactionRecord(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)


class EnergyLedgerRecord(Base):
    __tablename__ = "energy_ledger"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False)
    delta = Column(Float, nullable=False)
    reason = Column(String, nullable=False)


class DatabaseRuntime:
    def __init__(self, db_url: str | None = None) -> None:
        self.db_url = db_url or settings.DATABASE_URL
        self.enabled = bool(self.db_url)
        self.engine = create_engine(self.db_url, future=True) if self.enabled else None
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False) if self.engine else None

    def initialize(self) -> bool:
        if not self.enabled or not self.engine:
            return False
        Base.metadata.create_all(self.engine)
        return True
