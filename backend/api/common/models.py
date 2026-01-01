from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class GameState(str, enum.Enum):
    EDITABLE = "EDITABLE"
    SUBMITTED = "SUBMITTED"
    COACHING = "COACHING"
    COMPLETED = "COMPLETED"

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    state = Column(Enum(GameState), default=GameState.EDITABLE, nullable=False)
    
    player_color = Column(String)
    opponent_name = Column(String)
    event = Column(String)
    date = Column(DateTime)
    time_control = Column(String)
    pgn = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    annotations = relationship("Annotation", back_populates="game", cascade="all, delete-orphan")
    key_positions = relationship("KeyPosition", back_populates="game", cascade="all, delete-orphan")
    reflection = Column(JSON) # AI generated reflection

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    move_number = Column(Integer, nullable=False)
    content = Column(String)
    
    # DB constraint for immutability check can be added in logic
    # but we track if it's frozen
    frozen = Column(Boolean, default=False, nullable=False)

    game = relationship("Game", back_populates="annotations")

class KeyPosition(Base):
    __tablename__ = "key_positions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    fen = Column(String, nullable=False)
    reason_code = Column(String)
    engine_truth = Column(JSON) # Evaluation, Best Move, Threats
    order = Column(Integer, nullable=False)

    game = relationship("Game", back_populates="key_positions")
    questions = relationship("Question", back_populates="key_position", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    key_position_id = Column(Integer, ForeignKey("key_positions.id"), nullable=False)
    category = Column(String, nullable=False) # OPP_INTENT, THREAT, etc.
    question_text = Column(String)
    answer_text = Column(String)
    skipped = Column(Boolean, default=False)
    order = Column(Integer, nullable=False)

    key_position = relationship("KeyPosition", back_populates="questions")

class ParentApproval(Base):
    __tablename__ = "parent_approvals"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    tier = Column(String, nullable=False) # STANDARD, ADVANCED
    approved = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False) # e.g., "OPENAI_API_KEY"
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
