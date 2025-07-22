import os
import tempfile
import httpx
from openai import OpenAI
from typing import Dict, Optional
from ..config import settings


class PodcastProcessor:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.http_client = httpx.Client(timeout=httpx.Timeout(300.0), follow_redirects=True)
    
    async def download_audio(self, audio_url: str) -> str:
        """Download audio file to temporary location"""
        try:
            response = self.http_client.get(audio_url)
            response.raise_for_status()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name
        except Exception as e:
            raise Exception(f"Failed to download audio: {str(e)}")
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            return transcript.text
        except Exception as e:
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    async def generate_summary_and_translate(self, transcript: str, episode_title: str) -> str:
        """Generate English summary and translate to Mandarin"""
        try:
            prompt = f"""
Please analyze this podcast transcript and perform two tasks:

1. Create a concise summary in English (300-400 words) that captures the key points, main arguments, and important insights.
2. Translate the summary to Simplified Chinese (Mandarin), ensuring the translation is natural and culturally appropriate.

Episode Title: {episode_title}

Transcript:
{transcript[:8000]}...  # Truncate for API limits

Please format your response exactly as follows:
ENGLISH_SUMMARY:
[Your English summary here]

中文摘要：
[Your Chinese translation here]
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a professional podcast summarizer and translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract the Mandarin summary
            full_response = response.choices[0].message.content
            if "中文摘要：" in full_response:
                mandarin_summary = full_response.split("中文摘要：")[1].strip()
                return mandarin_summary
            else:
                raise Exception("Failed to extract Mandarin summary from response")
                
        except Exception as e:
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    async def process_episode(self, episode_data: Dict) -> Optional[str]:
        """Process a single podcast episode"""
        audio_file_path = None
        try:
            # Download audio
            audio_file_path = await self.download_audio(episode_data['audio_url'])
            
            # Transcribe
            transcript = await self.transcribe_audio(audio_file_path)
            
            # Generate summary and translate
            mandarin_summary = await self.generate_summary_and_translate(
                transcript, 
                episode_data['title']
            )
            
            return mandarin_summary
            
        except Exception as e:
            print(f"Error processing episode {episode_data['title']}: {str(e)}")
            return None
            
        finally:
            # Clean up temporary file
            if audio_file_path and os.path.exists(audio_file_path):
                os.remove(audio_file_path)
    
    def __del__(self):
        if hasattr(self, 'http_client'):
            self.http_client.close()