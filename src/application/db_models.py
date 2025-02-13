import threading
import uuid

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLLITE_PATH = "sqlite:///agent_db.sqlite"


Base = declarative_base()


class GameState(Base):
    __tablename__ = "game_states"

    event_id = Column(String(length=64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_created_at = Column(Integer, nullable=False)
    event_data = Column(Text, nullable=True)


class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.engine = create_engine(SQLLITE_PATH)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()
