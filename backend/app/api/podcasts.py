from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Podcast
from pydantic import BaseModel

router = APIRouter()


class PodcastResponse(BaseModel):
    id: int
    name: str
    description: str | None
    cover_image_url: str | None
    
    class Config:
        from_attributes = True


@router.get("/podcasts", response_model=List[PodcastResponse])
async def get_podcasts(db: Session = Depends(get_db)):
    """Get all active podcasts for display on the website"""
    podcasts = db.query(Podcast).filter(Podcast.is_active == True).all()
    return podcasts