from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from .config import settings
from .database import SessionLocal, engine
from .models import Podcast, Episode, Newsletter
from .services.rss_parser import RSSParser
from .services.podcast_processor import PodcastProcessor
from .services.beehiiv import BeehiivService
import asyncio

# Initialize Celery
celery_app = Celery(
    'podcast_digest',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'weekly-newsletter': {
            'task': 'app.tasks.generate_weekly_newsletter',
            'schedule': crontab(hour=8, minute=0, day_of_week=0),  # Sunday 8 AM UTC
        },
    }
)


@celery_app.task
def process_single_podcast(podcast_id: int):
    """Process recent episodes from a single podcast"""
    db = SessionLocal()
    try:
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        if not podcast or not podcast.is_active:
            return
        
        # Parse RSS feed for recent episodes
        parser = RSSParser()
        recent_episodes = parser.get_recent_episodes(podcast.rss_url, days=7)
        
        # Process each episode
        processor = PodcastProcessor()
        processed_count = 0
        
        for episode_data in recent_episodes:
            # Check if episode already processed
            existing = db.query(Episode).filter(
                Episode.podcast_id == podcast.id,
                Episode.audio_url == episode_data['audio_url']
            ).first()
            
            if existing:
                continue
            
            # Process episode
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            mandarin_summary = loop.run_until_complete(
                processor.process_episode(episode_data)
            )
            loop.close()
            
            if mandarin_summary:
                # Save to database
                episode = Episode(
                    podcast_id=podcast.id,
                    title=episode_data['title'],
                    audio_url=episode_data['audio_url'],
                    publish_date=episode_data['publish_date'],
                    summary_mandarin=mandarin_summary
                )
                db.add(episode)
                processed_count += 1
        
        db.commit()
        return f"Processed {processed_count} episodes for {podcast.name}"
        
    except Exception as e:
        print(f"Error processing podcast {podcast_id}: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task
def generate_weekly_newsletter():
    """Generate and send weekly newsletter"""
    db = SessionLocal()
    try:
        # Get episodes from the past week
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        episodes = db.query(Episode).join(Podcast).filter(
            Episode.processed_at >= one_week_ago,
            Podcast.is_active == True
        ).order_by(Episode.publish_date.desc()).limit(10).all()
        
        if not episodes:
            print("No episodes to include in newsletter")
            return
        
        # Format episodes for newsletter
        episode_data = []
        for episode in episodes:
            episode_data.append({
                'podcast_name': episode.podcast.name,
                'title': episode.title,
                'audio_url': episode.audio_url,
                'summary_mandarin': episode.summary_mandarin
            })
        
        # Create newsletter with Beehiiv
        beehiiv = BeehiivService()
        content = beehiiv.format_newsletter_content(episode_data)
        
        # Schedule for next Sunday 9 AM
        next_sunday = datetime.now(timezone.utc)
        days_until_sunday = (6 - next_sunday.weekday()) % 7
        if days_until_sunday == 0:  # Today is Sunday
            days_until_sunday = 7
        next_sunday = next_sunday + timedelta(days=days_until_sunday)
        next_sunday = next_sunday.replace(hour=9, minute=0, second=0, microsecond=0)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            beehiiv.create_post(
                title=f"播客周报 - {datetime.now().strftime('%Y年%m月%d日')}",
                content=content,
                send_at=next_sunday
            )
        )
        loop.close()
        
        # Save newsletter record
        newsletter = Newsletter(
            beehiiv_post_id=result.get('id'),
            sent_at=next_sunday,
            episode_count=len(episodes)
        )
        db.add(newsletter)
        db.commit()
        
        return f"Newsletter created with {len(episodes)} episodes"
        
    except Exception as e:
        print(f"Error generating newsletter: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task
def process_all_podcasts():
    """Process all active podcasts"""
    db = SessionLocal()
    try:
        podcasts = db.query(Podcast).filter(Podcast.is_active == True).all()
        for podcast in podcasts:
            process_single_podcast.delay(podcast.id)
        return f"Started processing {len(podcasts)} podcasts"
    finally:
        db.close()