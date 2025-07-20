import httpx
from datetime import datetime
from typing import Dict, List, Optional
from ..config import settings


class BeehiivService:
    def __init__(self):
        self.api_key = settings.beehiiv_api_key
        self.publication_id = settings.beehiiv_publication_id
        self.base_url = "https://api.beehiiv.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.Client(headers=self.headers, timeout=30.0)
    
    async def create_post(self, title: str, content: str, send_at: Optional[datetime] = None) -> Dict:
        """Create a new post/newsletter in Beehiiv"""
        try:
            payload = {
                "title": title,
                "content": content,
                "status": "scheduled" if send_at else "draft",
                "publish_at": send_at.isoformat() if send_at else None,
                "email_subject": title,
                "preview_text": "本周精选播客摘要",
                "authors": ["Podcast Digest"],
            }
            
            response = self.client.post(
                f"{self.base_url}/publications/{self.publication_id}/posts",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error creating Beehiiv post: {str(e)}")
            raise
    
    def format_newsletter_content(self, episodes: List[Dict]) -> str:
        """Format episodes into newsletter HTML content"""
        content = """
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h1 style="color: #333; text-align: center; margin-bottom: 30px;">
        🎙️ 本周播客精选
    </h1>
    
    <p style="color: #666; font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
        欢迎阅读本周的播客摘要！我们为您精选了最有价值的英文播客内容，并翻译成中文摘要。
    </p>
"""
        
        for episode in episodes:
            content += f"""
    <div style="border-bottom: 1px solid #eee; padding: 20px 0; margin-bottom: 20px;">
        <h2 style="color: #333; margin-bottom: 10px;">
            📻 {episode['podcast_name']}
        </h2>
        <h3 style="color: #666; font-size: 18px; margin-bottom: 15px;">
            {episode['title']}
        </h3>
        <div style="color: #444; font-size: 16px; line-height: 1.8; margin-bottom: 15px;">
            {episode['summary_mandarin']}
        </div>
        <p style="margin-top: 15px;">
            <a href="{episode['audio_url']}" style="color: #007bff; text-decoration: none;">
                🎧 收听原版播客
            </a>
        </p>
    </div>
"""
        
        content += """
    <div style="text-align: center; margin-top: 40px; padding: 20px 0; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 14px;">
            感谢您的阅读！下周见 👋
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 10px;">
            Podcast Digest Team
        </p>
    </div>
</div>
"""
        return content
    
    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()