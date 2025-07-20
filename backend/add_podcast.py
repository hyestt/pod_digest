#!/usr/bin/env python3
"""
Command line script to add a new podcast to the database
Usage: python add_podcast.py
"""

from app.database import SessionLocal
from app.models import Podcast
from app.services.rss_parser import RSSParser


def add_podcast_interactive():
    """Interactive script to add a new podcast"""
    print("🎙️ Add New Podcast to Digest")
    print("=" * 40)
    
    # Get podcast details
    name = input("Podcast Name: ").strip()
    if not name:
        print("❌ Podcast name is required!")
        return
    
    rss_url = input("RSS Feed URL: ").strip()
    if not rss_url:
        print("❌ RSS URL is required!")
        return
    
    description = input("Description (optional): ").strip()
    cover_image_url = input("Cover Image URL (optional): ").strip()
    
    # Validate RSS feed
    print("\n🔍 Validating RSS feed...")
    parser = RSSParser()
    episodes = parser.parse_feed(rss_url)
    
    if not episodes:
        print("❌ Could not parse RSS feed or no episodes found!")
        return
    
    print(f"✅ Found {len(episodes)} episodes in the feed")
    print(f"Latest episode: {episodes[0]['title']}")
    
    # Confirm addition
    print(f"\n📋 Podcast Details:")
    print(f"Name: {name}")
    print(f"RSS URL: {rss_url}")
    print(f"Description: {description or 'None'}")
    print(f"Cover Image: {cover_image_url or 'None'}")
    
    confirm = input("\n➕ Add this podcast? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    # Add to database
    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.query(Podcast).filter(Podcast.rss_url == rss_url).first()
        if existing:
            print(f"❌ Podcast with this RSS URL already exists: {existing.name}")
            return
        
        # Create new podcast
        podcast = Podcast(
            name=name,
            description=description or None,
            rss_url=rss_url,
            cover_image_url=cover_image_url or None,
            is_active=True
        )
        
        db.add(podcast)
        db.commit()
        db.refresh(podcast)
        
        print(f"✅ Successfully added podcast: {podcast.name} (ID: {podcast.id})")
        
    except Exception as e:
        print(f"❌ Error adding podcast: {str(e)}")
        db.rollback()
    finally:
        db.close()


def list_podcasts():
    """List all podcasts in the database"""
    db = SessionLocal()
    try:
        podcasts = db.query(Podcast).all()
        
        if not podcasts:
            print("📭 No podcasts found in database")
            return
        
        print(f"\n📚 Current Podcasts ({len(podcasts)}):")
        print("=" * 50)
        
        for i, podcast in enumerate(podcasts, 1):
            status = "🟢 Active" if podcast.is_active else "🔴 Inactive"
            print(f"{i}. {podcast.name} {status}")
            print(f"   RSS: {podcast.rss_url}")
            print(f"   Description: {podcast.description or 'None'}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing podcasts: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_podcasts()
    else:
        add_podcast_interactive()