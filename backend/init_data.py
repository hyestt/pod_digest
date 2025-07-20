#!/usr/bin/env python3
"""
Script to initialize the database with sample podcast data
"""

from app.database import SessionLocal, engine
from app.models import Base, Podcast

# Sample podcast data
SAMPLE_PODCASTS = [
    {
        "name": "The Tim Ferriss Show",
        "description": "The Tim Ferriss Show is often the #1 business podcast on all of Apple Podcasts",
        "rss_url": "https://rss.art19.com/tim-ferriss-show",
        "cover_image_url": "https://cdn.megaphone.fm/podcasts/2d4ebdac-2e88-11e6-b532-43e2d5b76df5/image/uploads_2F1500915477653-v9l0pvcuhc9-a65c4e8fdf6b7b4f53e9c0b0a9b1bb74_2FTim_Ferriss_Show.jpg"
    },
    {
        "name": "TED Talks Daily",
        "description": "Every weekday, TED Talks Daily brings you the latest talks in audio",
        "rss_url": "https://feeds.feedburner.com/tedtalks_audio",
        "cover_image_url": "https://pi.tedcdn.com/r/talkstar-photos.s3.amazonaws.com/uploads/72bda52f-9bbf-4685-910a-2f151c4f3a8a/TED2019_20190410_1RL7834_1920.jpg"
    },
    {
        "name": "How I Built This with Guy Raz",
        "description": "Guy Raz dives into the stories behind some of the world's best known companies",
        "rss_url": "https://feeds.npr.org/510313/podcast.xml",
        "cover_image_url": "https://media.npr.org/assets/img/2018/08/03/npr_hibt_podcasttile_sq-bb0a5cdcce0ac2bc0b28c61a95c42e31a67b1cc6.jpg"
    },
    {
        "name": "The Daily",
        "description": "This is what the news should sound like. The biggest stories of our time",
        "rss_url": "https://feeds.simplecast.com/54nAGcIl",
        "cover_image_url": "https://static01.nyt.com/images/2017/01/29/podcasts/the-daily-album-art/the-daily-album-art-square320-v5.jpg"
    },
    {
        "name": "Planet Money",
        "description": "The economy explained. Imagine you could call up a friend and say...",
        "rss_url": "https://feeds.npr.org/510289/podcast.xml",
        "cover_image_url": "https://media.npr.org/assets/img/2018/08/02/npr_planetmoney_podcasttile_sq-7b7fab0b52fd72826936c3dbe51cff94889797a0.jpg"
    },
    {
        "name": "Freakonomics Radio",
        "description": "Discover the hidden side of everything with Stephen J. Dubner",
        "rss_url": "http://feeds.feedburner.com/freakonomicsradio",
        "cover_image_url": "https://cdn.megaphone.fm/podcasts/6b5bff88-ac09-11e7-a9b2-0be4ffb5c1e7/image/Freakonomics_Radio.png"
    }
]


def init_database():
    """Initialize database with sample data"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Add sample podcasts
    db = SessionLocal()
    try:
        # Check if podcasts already exist
        existing_count = db.query(Podcast).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} podcasts. Skipping initialization.")
            return
        
        # Add sample podcasts
        for podcast_data in SAMPLE_PODCASTS:
            podcast = Podcast(**podcast_data)
            db.add(podcast)
        
        db.commit()
        print(f"Successfully added {len(SAMPLE_PODCASTS)} sample podcasts to the database.")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()