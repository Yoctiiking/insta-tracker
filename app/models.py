"""
Modèles de la base de données.

Snapshot   -> une "photo" de l'état de tes abonnés/abonnements à un instant T
Relation   -> chaque compte présent dans ce snapshot (follower et/ou followee)
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    followers_count = Column(Integer)
    following_count = Column(Integer)

    relations = relationship("Relation", back_populates="snapshot", cascade="all, delete-orphan")


class Relation(Base):
    __tablename__ = "relations"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"))
    username = Column(String, index=True)
    full_name = Column(String, nullable=True)
    is_follower = Column(Boolean, default=False)   # cette personne te suit
    is_following = Column(Boolean, default=False)  # tu suis cette personne
    profile_pic_url = Column(String, nullable=True)

    snapshot = relationship("Snapshot", back_populates="relations")
