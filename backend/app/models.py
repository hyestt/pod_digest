from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Podcast(Base):
    __tablename__ = "podcasts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cover_image_url = Column(Text)
    rss_url = Column(Text, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    episodes = relationship("Episode", back_populates="podcast")


class Episode(Base):
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True, index=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"))
    title = Column(String(255))
    audio_url = Column(Text)
    publish_date = Column(DateTime(timezone=True))
    summary_mandarin = Column(Text)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    podcast = relationship("Podcast", back_populates="episodes")


class Newsletter(Base):
    __tablename__ = "newsletters"
    
    id = Column(Integer, primary_key=True, index=True)
    beehiiv_post_id = Column(String(255))
    sent_at = Column(DateTime(timezone=True))
    episode_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())