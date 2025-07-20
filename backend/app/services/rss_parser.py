import feedparser
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import httpx


class RSSParser:
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def parse_feed(self, rss_url: str) -> List[Dict]:
        """Parse RSS feed and return list of episodes"""
        try:
            feed = feedparser.parse(rss_url)
            episodes = []
            
            for entry in feed.entries:
                # Extract audio URL (usually in enclosures)
                audio_url = None
                if hasattr(entry, 'enclosures') and entry.enclosures:
                    for enclosure in entry.enclosures:
                        if enclosure.get('type', '').startswith('audio'):
                            audio_url = enclosure.get('href')
                            break
                
                # Parse publish date
                publish_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    publish_date = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed),
                        tz=timezone.utc
                    )
                
                if audio_url:
                    episodes.append({
                        'title': entry.get('title', 'Untitled'),
                        'description': entry.get('description', ''),
                        'audio_url': audio_url,
                        'publish_date': publish_date,
                        'guid': entry.get('id', audio_url),
                    })
            
            return episodes
        except Exception as e:
            print(f"Error parsing RSS feed {rss_url}: {str(e)}")
            return []
    
    def get_recent_episodes(self, rss_url: str, days: int = 7) -> List[Dict]:
        """Get episodes published in the last N days"""
        episodes = self.parse_feed(rss_url)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        recent_episodes = []
        for episode in episodes:
            if episode['publish_date'] and episode['publish_date'] > cutoff_date:
                recent_episodes.append(episode)
        
        return recent_episodes
    
    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()