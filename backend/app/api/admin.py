from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Podcast
from ..services.rss_parser import RSSParser
from pydantic import BaseModel, HttpUrl
import feedparser

router = APIRouter()


class PodcastCreate(BaseModel):
    name: str
    description: str | None = None
    rss_url: HttpUrl
    cover_image_url: HttpUrl | None = None


class PodcastCreateFromRSS(BaseModel):
    rss_url: HttpUrl


class PodcastUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rss_url: HttpUrl | None = None
    cover_image_url: HttpUrl | None = None
    is_active: bool | None = None


class PodcastResponse(BaseModel):
    id: int
    name: str
    description: str | None
    rss_url: str
    cover_image_url: str | None
    is_active: bool
    
    class Config:
        from_attributes = True


@router.post("/podcasts", response_model=PodcastResponse)
async def create_podcast(podcast: PodcastCreate, db: Session = Depends(get_db)):
    """Add a new podcast to the system"""
    # Check if RSS URL already exists
    existing = db.query(Podcast).filter(Podcast.rss_url == str(podcast.rss_url)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Podcast with this RSS URL already exists")
    
    db_podcast = Podcast(
        name=podcast.name,
        description=podcast.description,
        rss_url=str(podcast.rss_url),
        cover_image_url=str(podcast.cover_image_url) if podcast.cover_image_url else None
    )
    
    db.add(db_podcast)
    db.commit()
    db.refresh(db_podcast)
    
    return db_podcast


@router.post("/podcasts/from-rss", response_model=PodcastResponse)
async def create_podcast_from_rss(podcast: PodcastCreateFromRSS, db: Session = Depends(get_db)):
    """Add a new podcast by automatically parsing RSS feed information"""
    rss_url = str(podcast.rss_url)
    
    # Check if RSS URL already exists
    existing = db.query(Podcast).filter(Podcast.rss_url == rss_url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Podcast with this RSS URL already exists")
    
    try:
        # Parse RSS feed to get podcast information
        feed = feedparser.parse(rss_url)
        
        if not feed.feed:
            raise HTTPException(status_code=400, detail="Invalid RSS feed or feed not accessible")
        
        # Extract podcast information from RSS feed
        podcast_name = feed.feed.get('title', 'Unknown Podcast')
        podcast_description = feed.feed.get('description', feed.feed.get('subtitle', ''))
        
        # Try to get cover image from various possible fields
        cover_image_url = None
        if hasattr(feed.feed, 'image') and feed.feed.image:
            cover_image_url = feed.feed.image.get('href')
        elif hasattr(feed.feed, 'logo'):
            cover_image_url = feed.feed.logo
        elif hasattr(feed.feed, 'itunes_image') and feed.feed.itunes_image:
            cover_image_url = feed.feed.itunes_image.get('href')
        
        # Create new podcast with extracted information
        db_podcast = Podcast(
            name=podcast_name,
            description=podcast_description,
            rss_url=rss_url,
            cover_image_url=cover_image_url,
            is_active=True
        )
        
        db.add(db_podcast)
        db.commit()
        db.refresh(db_podcast)
        
        return db_podcast
        
    except Exception as e:
        if "RSS URL already exists" in str(e):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to parse RSS feed: {str(e)}")


@router.get("/podcasts", response_model=List[PodcastResponse])
async def list_all_podcasts(db: Session = Depends(get_db)):
    """Get all podcasts (including inactive ones)"""
    podcasts = db.query(Podcast).all()
    return podcasts


@router.put("/podcasts/{podcast_id}", response_model=PodcastResponse)
async def update_podcast(podcast_id: int, podcast: PodcastUpdate, db: Session = Depends(get_db)):
    """Update an existing podcast"""
    db_podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not db_podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    
    # Update fields if provided
    if podcast.name is not None:
        db_podcast.name = podcast.name
    if podcast.description is not None:
        db_podcast.description = podcast.description
    if podcast.rss_url is not None:
        db_podcast.rss_url = str(podcast.rss_url)
    if podcast.cover_image_url is not None:
        db_podcast.cover_image_url = str(podcast.cover_image_url)
    if podcast.is_active is not None:
        db_podcast.is_active = podcast.is_active
    
    db.commit()
    db.refresh(db_podcast)
    
    return db_podcast


@router.delete("/podcasts/{podcast_id}")
async def delete_podcast(podcast_id: int, db: Session = Depends(get_db)):
    """Delete a podcast (or mark as inactive)"""
    db_podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not db_podcast:
        raise HTTPException(status_code=404, detail="Podcast not found")
    
    # Mark as inactive instead of deleting
    db_podcast.is_active = False
    db.commit()
    
    return {"message": "Podcast deactivated successfully"}