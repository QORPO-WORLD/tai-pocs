import uuid
from sqlalchemy import Column, Integer, String, JSON, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import threading
from alembic import command
from alembic.config import Config
import os

SQLLITE_PATH = 'sqlite:///agent_service_db.sqlite3'


Base = declarative_base()

class GameState(Base):
    __tablename__ = 'game_states'

    event_id = Column(String(length=64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_created_at = Column(Integer, nullable=False)
    event_send_at = Column(Integer, nullable=False)
    event_data = Column(JSON, nullable=True)  # Use JSON to store structured data
    processed_data = Column(JSON, nullable=True)

    def __repr__(self):
        return (f"<GameState(event_id={self.event_id}, event_created_at={self.event_created_at}, "
                f"event_send_at={self.event_send_at}, event_data={self.event_data}, "
                f"processed_data={self.processed_data})>")

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
        self.engine = create_engine('sqlite:///agent_db.sqlite')
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self._setup_migrations()

    def get_session(self):
        return self.SessionLocal()

    def _setup_migrations(self):
        # Create an Alembic directory if it doesn't exist
        if not os.path.exists("alembic.ini"):
            print("Setting up Alembic configuration...")
            # Generate a default alembic.ini file and migration directory
            alembic_cfg = Config()
            alembic_cfg.set_main_option("sqlalchemy.url", SQLLITE_PATH)
            alembic_cfg.set_main_option("script_location", "alembic")

            if not os.path.exists("alembic"):
                os.makedirs("alembic/versions")
                print("Created Alembic migration directory.")

    def run_migrations(self, message="Auto migration"):
        # Run Alembic migration generation and upgrade
        alembic_cfg = Config("alembic.ini")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        command.upgrade(alembic_cfg, "head")



def main():
    db = DatabaseConnection()
    db.run_migrations()
    session = db.get_session()
    # Create a new game state
    game_state = GameState(event_created_at=0, event_send_at=0, event_data={"message": "Hello, world!"})
    session.add(game_state)
    session.commit()
    print("Game state created successfully!")
    session.close()

if __name__ == "__main__":
    main()