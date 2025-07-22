#!/usr/bin/env python3
"""
統一的Podcast處理腳本 - 增強轉錄版本
支援：
1. 列出所有episodes及標題
2. 處理特定日期區間的episodes
3. 只轉錄，不生成摘要
"""

import os
import sys
import time
import re
import argparse
import tempfile
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 嘗試導入所需的包
try:
    import feedparser
    import httpx
    from openai import OpenAI
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請安裝必要的依賴: pip install feedparser httpx openai")
    sys.exit(1)

# 嘗試導入音頻處理包（用於大文件切割）
try:
    from pydub import AudioSegment
    AUDIO_SPLITTING_AVAILABLE = True
    print("✅ 音頻切割功能可用")
except ImportError as e:
    AUDIO_SPLITTING_AVAILABLE = False
    print(f"💡 音頻切割功能不可用: {e}")
    print("💡 解決方案:")
    print("   1. 安裝依賴: pip install pydub")
    print("   2. 安裝 ffmpeg:")
    print("      - macOS: brew install ffmpeg")
    print("      - Ubuntu: sudo apt install ffmpeg") 
    print("      - Windows: 下載 ffmpeg 並添加到 PATH")


class UnifiedPodcastProcessor:
    """統一的Podcast處理器 - 增強轉錄版本"""
    
    def __init__(self):
        # 檢查OpenAI API Key
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("請設置 OPENAI_API_KEY 環境變量")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # 設置數據庫路徑
        self.db_path = "backend/test.db"
        
        # 確保基本輸出目錄存在
        self.audio_dir = Path("downloads/audio")
        self.transcripts_base_dir = Path("downloads/transcripts")
        
        # 創建基本目錄
        for directory in [self.audio_dir, self.transcripts_base_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def sanitize_filename(self, filename):
        """清理文件名"""
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 100:
            filename = filename[:100]
        return filename
    
    def parse_date(self, date_string):
        """解析各種日期格式為 datetime 對象"""
        from email.utils import parsedate_to_datetime
        
        try:
            # 嘗試 RFC 2822 格式（RSS 常用）
            return parsedate_to_datetime(date_string)
        except:
            pass
        
        # 嘗試其他常見格式
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%B %d, %Y",
            "%d %B %Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]
        
        for fmt in date_formats:
            try:
                # 解析為 naive datetime，然後添加時區
                dt = datetime.strptime(date_string.strip(), fmt)
                # 假設為 UTC 時區
                return dt.replace(tzinfo=timezone.utc)
            except:
                continue
        
        # 如果都失敗，嘗試 dateutil
        try:
            import dateutil.parser
            dt = dateutil.parser.parse(date_string)
            if dt.tzinfo is None:
                # 如果沒有時區信息，假設為 UTC
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except:
            return None
    
    def parse_podcast_publish_date(self, publish_date, podcast_name=""):
        """解析播客發布日期，確保使用實際發布日期而非下載日期"""
        
        # 如果沒有發布日期信息
        if not publish_date or publish_date in ['Unknown', '', None]:
            print(f"  ⚠️ 警告: {podcast_name} 沒有提供發布日期信息")
            return f"unknown-{datetime.now().strftime('%Y-%m-%d')}"
        
        date_obj = self.parse_date(publish_date)
        if date_obj:
            result = date_obj.strftime('%Y-%m-%d')
            print(f"  ✅ 成功解析發布日期: {publish_date} -> {result}")
            return result
        else:
            print(f"  ⚠️ 無法解析日期: {publish_date}")
            return f"unknown-{datetime.now().strftime('%Y-%m-%d')}"
    
    def get_podcasts_from_db(self):
        """從數據庫獲取podcasts列表"""
        podcasts = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, rss_url, description, is_active 
                FROM podcasts 
                WHERE is_active = 1
                ORDER BY name
            """)
            
            for row in cursor.fetchall():
                podcasts.append({
                    'name': row[0],
                    'rss_url': row[1],
                    'description': row[2],
                    'is_active': row[3]
                })
            
            conn.close()
        except Exception as e:
            print(f"  ⚠️ 讀取數據庫失敗: {e}")
            # 返回默認列表
            podcasts = [
                {
                    'name': 'Acquired',
                    'rss_url': 'https://feeds.transistor.fm/acquired',
                    'description': 'Acquired is the podcast about great companies',
                    'is_active': True
                },
                {
                    'name': 'The Journal.',
                    'rss_url': 'https://video-api.wsj.com/podcast/rss/wsj/the-journal',
                    'description': 'The most important stories about money, business and power',
                    'is_active': True
                },
                {
                    'name': 'Planet Money',
                    'rss_url': 'https://feeds.npr.org/510289/podcast.xml',
                    'description': "NPR's Planet Money. The economy, explained.",
                    'is_active': True
                }
            ]
        
        return podcasts
    
    def find_podcast_by_name(self, name):
        """根據名稱查找podcast"""
        podcasts = self.get_podcasts_from_db()
        for podcast in podcasts:
            if podcast['name'].lower() == name.lower():
                return podcast
        return None
    
    def parse_rss_feed(self, rss_url):
        """解析RSS feed並返回episodes列表"""
        try:
            # 獲取RSS內容
            with httpx.Client(timeout=30.0) as client:
                response = client.get(rss_url)
                response.raise_for_status()
            
            # 解析feed
            feed = feedparser.parse(response.content)
            
            episodes = []
            for entry in feed.entries:
                # 找音頻URL
                audio_url = None
                for enclosure in entry.get('enclosures', []):
                    if enclosure.get('type', '').startswith('audio'):
                        audio_url = enclosure.get('href')
                        break
                
                if not audio_url:
                    for link in entry.get('links', []):
                        if link.get('type', '').startswith('audio'):
                            audio_url = link.get('href')
                            break
                
                if audio_url:
                    # 解析發布日期
                    publish_date = entry.get('published', entry.get('pubDate', ''))
                    date_obj = self.parse_date(publish_date) if publish_date else None
                    
                    episodes.append({
                        'title': entry.get('title', 'Unknown Title'),
                        'publish_date': publish_date,
                        'date_obj': date_obj,  # 添加解析後的日期對象
                        'audio_url': audio_url,
                        'description': entry.get('summary', '')[:500],  # 限制描述長度
                        'duration': entry.get('itunes_duration', '')
                    })
            
            return episodes
        
        except Exception as e:
            print(f"  ❌ 解析RSS失敗: {e}")
            return []
    
    def list_episodes(self, podcast_name, start_date=None, end_date=None):
        """列出podcast的所有episodes，可選日期篩選"""
        podcast = self.find_podcast_by_name(podcast_name)
        if not podcast:
            print(f"❌ 未找到podcast: {podcast_name}")
            return []
        
        print(f"\n📡 獲取 {podcast['name']} 的episode列表...")
        episodes = self.parse_rss_feed(podcast['rss_url'])
        
        if not episodes:
            print("❌ 無法獲取episode列表")
            return []
        
        # 日期篩選
        if start_date or end_date:
            filtered_episodes = []
            for ep in episodes:
                if ep['date_obj']:
                    # 確保日期比較時都有時區信息
                    ep_date = ep['date_obj']
                    if ep_date.tzinfo is None:
                        ep_date = ep_date.replace(tzinfo=timezone.utc)
                    
                    if start_date:
                        start_dt = start_date
                        if start_dt.tzinfo is None:
                            start_dt = start_dt.replace(tzinfo=timezone.utc)
                        if ep_date < start_dt:
                            continue
                    
                    if end_date:
                        end_dt = end_date
                        if end_dt.tzinfo is None:
                            end_dt = end_dt.replace(tzinfo=timezone.utc)
                        # 包含結束日期當天
                        end_dt = end_dt.replace(hour=23, minute=59, second=59)
                        if ep_date > end_dt:
                            continue
                    
                    filtered_episodes.append(ep)
            episodes = filtered_episodes
        
        print(f"\n📋 {podcast['name']} Episode列表")
        if start_date or end_date:
            date_range = f"{start_date.strftime('%Y-%m-%d') if start_date else '開始'} 到 {end_date.strftime('%Y-%m-%d') if end_date else '現在'}"
            print(f"📅 日期範圍: {date_range}")
        print(f"📊 總共: {len(episodes)} 集\n")
        
        for i, episode in enumerate(episodes):
            date_str = episode['date_obj'].strftime('%Y-%m-%d') if episode['date_obj'] else '未知日期'
            duration_str = f" [{episode['duration']}]" if episode['duration'] else ""
            print(f"{i:3d}. [{date_str}] {episode['title']}{duration_str}")
        
        return episodes
    
    def process_date_range(self, podcast_name, start_date, end_date):
        """處理指定日期範圍內的所有episodes"""
        episodes = self.list_episodes(podcast_name, start_date, end_date)
        
        if not episodes:
            print("沒有找到符合條件的episodes")
            return
        
        print(f"\n準備處理 {len(episodes)} 集節目")
        confirm = input("確認處理？(y/n): ")
        
        if confirm.lower() != 'y':
            print("取消處理")
            return
        
        # 逐個處理
        for i, episode in enumerate(episodes):
            print(f"\n{'='*50}")
            print(f"處理第 {i+1}/{len(episodes)} 集")
            print(f"{'='*50}")
            
            # 使用原有的處理邏輯，但傳入特定的episode
            self.process_specific_episode(podcast_name, episode)
            
            # 避免過於頻繁的API調用
            if i < len(episodes) - 1:
                print("\n⏳ 等待5秒後處理下一集...")
                time.sleep(5)
    
    def process_multiple_episodes(self, podcast_name, episode_indices):
        """處理多個指定的 episode 集數"""
        podcast = self.find_podcast_by_name(podcast_name)
        if not podcast:
            print(f"❌ 未找到podcast: {podcast_name}")
            return
        
        print(f"\n📡 獲取 {podcast['name']} 的episode列表...")
        episodes = self.parse_rss_feed(podcast['rss_url'])
        
        if not episodes:
            print("❌ 無法獲取episode列表")
            return
        
        # 驗證所有索引是否有效
        invalid_indices = [i for i in episode_indices if i >= len(episodes)]
        if invalid_indices:
            print(f"❌ 以下episode索引超出範圍 (總共{len(episodes)}集): {invalid_indices}")
            return
        
        # 顯示將要處理的episodes
        print(f"\n📋 準備處理以下 {len(episode_indices)} 集:")
        for i, idx in enumerate(episode_indices):
            episode = episodes[idx]
            date_str = episode['date_obj'].strftime('%Y-%m-%d') if episode['date_obj'] else '未知日期'
            print(f"  {i+1}. [{idx}] [{date_str}] {episode['title']}")
        
        confirm = input("\n確認處理？(y/n): ")
        if confirm.lower() != 'y':
            print("取消處理")
            return
        
        # 處理每個episode
        for i, idx in enumerate(episode_indices):
            episode = episodes[idx]
            print(f"\n{'='*50}")
            print(f"處理第 {i+1}/{len(episode_indices)} 集 (索引 {idx})")
            print(f"{'='*50}")
            
            self.process_specific_episode(podcast_name, episode)
            
            # 避免過於頻繁的API調用
            if i < len(episode_indices) - 1:
                print("\n⏳ 等待5秒後處理下一集...")
                time.sleep(5)
    
    def process_specific_episode(self, podcast_name, episode):
        """處理特定的episode（從list_episodes獲得的episode對象）"""
        podcast = self.find_podcast_by_name(podcast_name)
        if not podcast:
            return
        
        print(f"\n🎯 處理episode: {episode['title']}")
        print(f"📅 發布日期: {episode['publish_date']}")
        
        # 創建目錄結構
        print("\n📁 創建目錄結構...")
        directories = self.create_podcast_directories(episode, podcast['name'])
        
        # 下載音頻
        print(f"\n⬇️ 步驟1: 下載音頻文件")
        audio_filepath = self.download_audio(episode['audio_url'])
        
        if not audio_filepath:
            print("❌ 音頻下載失敗，跳過此集")
            return
        
        try:
            # 獲取文件大小
            file_size = os.path.getsize(audio_filepath)
            
            # 轉錄音頻
            print(f"\n🎤 步驟2: 轉錄音頻")
            transcript, transcript_time = self.transcribe_audio_file(audio_filepath)
            
            if not transcript:
                print("❌ 轉錄失敗")
                return
            
            # 保存轉錄
            print(f"\n💾 步驟3: 保存轉錄文件")
            transcript_filepath = self.save_transcript(
                transcript, episode, podcast['name'], 
                transcript_time, file_size, directories
            )
            
            # 完成
            total_time = time.time() - directories['start_time']
            print(f"\n🎉 處理完成!")
            print(f"📁 轉錄文件: {transcript_filepath}")
            print(f"⏱️ 總耗時: {total_time:.1f} 秒")
            
        except Exception as e:
            print(f"❌ 處理過程中發生錯誤: {e}")
        finally:
            # 清理臨時音頻文件
            try:
                if os.path.exists(audio_filepath):
                    os.remove(audio_filepath)
                    print(f"🗑️ 已清理臨時文件")
            except:
                pass
    
    def create_podcast_directories(self, episode, podcast_name):
        """創建podcast專屬目錄結構"""
        # 解析發布日期
        publish_date_str = self.parse_podcast_publish_date(
            episode.get('publish_date', ''), 
            podcast_name
        )
        
        print(f"  📅 使用發布日期: {publish_date_str}")
        
        # 創建目錄名稱：日期_Podcast名稱
        dir_name = f"{publish_date_str}_{podcast_name.replace(' ', '_')}"
        print(f"  📂 目錄名稱: {dir_name}")
        
        # 創建目錄結構
        transcript_dir = self.transcripts_base_dir / podcast_name / dir_name
        
        # 創建語言子目錄
        transcript_english_dir = transcript_dir / 'english'
        
        # 創建所有目錄
        transcript_english_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  📂 目錄結構: {podcast_name}/{dir_name}/english")
        
        return {
            'transcript_dir': transcript_dir,
            'transcript_english_dir': transcript_english_dir,
            'start_time': time.time()
        }
    
    def download_audio(self, audio_url):
        """下載音頻文件"""
        try:
            # 創建臨時文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            temp_filepath = temp_file.name
            temp_file.close()
            
            print(f"📥 開始下載: {os.path.basename(temp_filepath)}")
            
            start_time = time.time()
            downloaded = 0
            
            with httpx.Client(timeout=300.0, follow_redirects=True) as client:
                with client.stream('GET', audio_url) as response:
                    response.raise_for_status()
                    
                    with open(temp_filepath, 'wb') as f:
                        for chunk in response.iter_bytes(chunk_size=1024*1024):  # 1MB chunks
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                mb_downloaded = downloaded / (1024 * 1024)
                                
                                # 每10MB顯示一次進度
                                if int(mb_downloaded) % 10 == 0 and mb_downloaded > 0:
                                    print(f"  📊 {mb_downloaded:.1f}MB...")
            
            # 檢查文件
            file_size = os.path.getsize(temp_filepath)
            download_time = time.time() - start_time
            download_speed = (file_size / (1024 * 1024)) / download_time
            
            print(f"  ✅ 下載完成!")
            print(f"  📏 大小: {file_size / (1024 * 1024):.1f}MB")
            print(f"  ⏱️ 時間: {download_time:.1f}秒")
            print(f"  🚀 速度: {download_speed:.1f}MB/s")
            
            return temp_filepath
            
        except Exception as e:
            print(f"  ❌ 下載失敗: {e}")
            if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return None
    
    def transcribe_audio_file(self, audio_filepath):
        """轉錄音頻文件（處理大文件）"""
        start_time = time.time()
        file_size = os.path.getsize(audio_filepath)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"🎤 開始轉錄音頻...")
        
        # Whisper API 限制 25MB
        MAX_FILE_SIZE_MB = 24  # 留點餘地
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            print(f"  📏 文件大小: {file_size_mb:.1f}MB，超過限制，開始切割處理...")
            
            if AUDIO_SPLITTING_AVAILABLE:
                # 使用 pydub 切割
                return self.transcribe_large_audio_with_pydub(audio_filepath)
            else:
                # 使用簡單的二進制切割
                print(f"  ❌ 自動音頻切割功能不可用")
                print(f"  💡 替代方案: 使用二進制切割方法...")
                return self.transcribe_large_audio_binary_split(audio_filepath)
        else:
            # 直接轉錄
            try:
                with open(audio_filepath, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                
                transcribe_time = time.time() - start_time
                text = transcript.text
                
                print(f"  ✅ 轉錄完成!")
                print(f"  ⏱️ 轉錄耗時: {transcribe_time:.1f} 秒")
                print(f"  📝 字符數: {len(text):,}")
                print(f"  📊 單詞數: {len(text.split()):,}")
                
                return text, transcribe_time
                
            except Exception as e:
                print(f"  ❌ 轉錄失敗: {e}")
                return None, 0
    
    def transcribe_large_audio_with_pydub(self, audio_filepath):
        """使用pydub切割並轉錄大音頻文件"""
        start_time = time.time()
        
        try:
            # 加載音頻
            print(f"  📂 加載音頻文件...")
            audio = AudioSegment.from_mp3(audio_filepath)
            
            # 計算需要的片段數
            duration_ms = len(audio)
            # 每個片段20分鐘（通常會小於24MB）
            chunk_length_ms = 20 * 60 * 1000
            chunks = []
            
            print(f"  ⏱️ 音頻總長度: {duration_ms / 1000 / 60:.1f} 分鐘")
            print(f"  ✂️ 開始切割音頻...")
            
            # 切割音頻
            for i in range(0, duration_ms, chunk_length_ms):
                chunk = audio[i:i + chunk_length_ms]
                chunk_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                chunk.export(chunk_file.name, format='mp3')
                chunks.append(chunk_file.name)
                print(f"    📋 片段{len(chunks)}: {len(chunk) / 1000 / 60:.1f} 分鐘")
            
            print(f"  ✅ 成功切割為{len(chunks)}個片段")
            
            # 轉錄每個片段
            all_transcripts = []
            for i, chunk_path in enumerate(chunks):
                print(f"  🎤 轉錄片段 {i+1}/{len(chunks)}...")
                try:
                    with open(chunk_path, 'rb') as audio_file:
                        transcript = self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="en"
                        )
                    all_transcripts.append(transcript.text)
                    print(f"    ✅ 片段{i+1}完成: {len(transcript.text):,}字符")
                except Exception as e:
                    print(f"    ❌ 片段{i+1}轉錄失敗: {e}")
                    all_transcripts.append("")
                finally:
                    # 清理片段文件
                    try:
                        os.remove(chunk_path)
                    except:
                        pass
            
            # 合併轉錄結果
            full_transcript = " ".join(all_transcripts)
            transcribe_time = time.time() - start_time
            
            print(f"  ✅ 分段轉錄完成!")
            print(f"  ⏱️ 總轉錄耗時: {transcribe_time:.1f} 秒")
            print(f"  📝 總字符數: {len(full_transcript):,}")
            print(f"  📊 總單詞數: {len(full_transcript.split()):,}")
            
            return full_transcript, transcribe_time
            
        except Exception as e:
            print(f"  ❌ pydub處理失敗: {e}")
            return None, 0
    
    def transcribe_large_audio_binary_split(self, audio_filepath):
        """使用二進制切割處理大音頻文件"""
        start_time = time.time()
        file_size = os.path.getsize(audio_filepath)
        
        # 每個片段最大 24MB
        MAX_CHUNK_SIZE = 24 * 1024 * 1024
        
        print(f"  📏 原始文件大小: {file_size / (1024*1024):.1f}MB")
        print(f"  ✂️ 開始二進制切割 (每個片段約24MB)...")
        
        # 切割文件
        chunks = []
        with open(audio_filepath, 'rb') as f:
            chunk_num = 0
            while True:
                chunk_data = f.read(MAX_CHUNK_SIZE)
                if not chunk_data:
                    break
                
                chunk_num += 1
                chunk_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                chunk_file.write(chunk_data)
                chunk_file.close()
                
                chunk_size_mb = len(chunk_data) / (1024 * 1024)
                print(f"    📋 片段{chunk_num}: {chunk_size_mb:.1f}MB")
                chunks.append(chunk_file.name)
        
        print(f"  ✅ 成功切割為{len(chunks)}個片段")
        print(f"  ⚠️ 注意: 二進制切割可能在音頻邊界處產生輕微失真")
        
        # 轉錄每個片段
        all_transcripts = []
        for i, chunk_path in enumerate(chunks):
            print(f"  🎤 轉錄片段 {i+1}/{len(chunks)}...")
            try:
                with open(chunk_path, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                all_transcripts.append(transcript.text)
                print(f"    ✅ 片段{i+1}完成: {len(transcript.text):,}字符, {len(transcript.text.split()):,}單詞")
            except Exception as e:
                print(f"    ❌ 片段{i+1}轉錄失敗: {e}")
                all_transcripts.append("")
            finally:
                # 清理片段文件
                try:
                    os.remove(chunk_path)
                except:
                    pass
        
        # 合併轉錄結果
        full_transcript = " ".join(all_transcripts)
        transcribe_time = time.time() - start_time
        
        print(f"  ✅ 分段轉錄完成!")
        print(f"  📦 處理了{len(chunks)}個片段")
        print(f"  ⏱️ 總轉錄耗時: {transcribe_time:.1f} 秒")
        print(f"  📝 總字符數: {len(full_transcript):,}")
        print(f"  📊 總單詞數: {len(full_transcript.split()):,}")
        
        return full_transcript, transcribe_time
    
    def save_transcript(self, transcript, episode, podcast_name, transcript_time, file_size, directories):
        """保存轉錄文件到podcast專屬目錄"""
        safe_title = self.sanitize_filename(episode['title'])
        timestamp = datetime.now().strftime('%H%M')
        
        filename = f"{safe_title}_{timestamp}_transcript.txt"
        filepath = directories['transcript_english_dir'] / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {podcast_name} 播客轉錄文字稿\n")
            f.write(f"集數標題: {episode['title']}\n")
            f.write(f"發布日期: {episode['publish_date']}\n")
            f.write(f"音頻URL: {episode['audio_url']}\n")
            f.write(f"轉錄時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"轉錄耗時: {transcript_time:.1f} 秒\n")
            f.write(f"文件大小: {file_size / (1024*1024):.1f} MB\n")
            f.write(f"字符數: {len(transcript):,}\n")
            f.write(f"單詞數: {len(transcript.split()):,}\n")
            f.write(f"使用模型: whisper-1\n")
            f.write("\n" + "="*50 + "\n")
            f.write("轉錄內容:\n")
            f.write("="*50 + "\n\n")
            f.write(transcript)
        
        try:
            relative_path = filepath.relative_to(Path.cwd())
            print(f"  📄 英文轉錄文件已保存: {relative_path}")
        except ValueError:
            print(f"  📄 英文轉錄文件已保存: {filepath}")
        return filepath
    
    def process_podcast_episode(self, podcast_name=None, episode_index=0):
        """處理指定podcast的指定集數"""
        print(f"🎙️ 統一Podcast處理器 - 增強轉錄版本")
        print("=" * 50)
        
        # 獲取podcast
        if podcast_name:
            podcast = self.find_podcast_by_name(podcast_name)
            if not podcast:
                print(f"❌ 未找到podcast: {podcast_name}")
                return
        else:
            podcasts = self.get_podcasts_from_db()
            if not podcasts:
                print("❌ 數據庫中沒有活躍的podcast")
                return
            
            print("📋 可用的podcast:")
            for i, p in enumerate(podcasts):
                print(f"  {i+1}. {p['name']}")
            
            try:
                choice = int(input("\n請選擇要處理的podcast (輸入數字): ")) - 1
                if 0 <= choice < len(podcasts):
                    podcast = podcasts[choice]
                else:
                    print("❌ 無效選擇")
                    return
            except (ValueError, KeyboardInterrupt):
                print("❌ 操作取消")
                return
        
        print(f"\n📡 處理podcast: {podcast['name']}")
        print(f"🔗 RSS: {podcast['rss_url']}")
        
        # 獲取episodes
        print("📡 獲取episode列表...")
        episodes = self.parse_rss_feed(podcast['rss_url'])
        
        if not episodes:
            print("❌ 無法獲取episode列表")
            return
        
        if episode_index >= len(episodes):
            print(f"❌ episode索引超出範圍 (總共{len(episodes)}集)")
            return
        
        episode = episodes[episode_index]
        self.process_specific_episode(podcast['name'], episode)


def parse_date_range(date_str):
    """解析日期或日期範圍字符串"""
    # 支援的日期格式
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
    ]
    
    # 嘗試解析單個日期
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # 添加 UTC 時區
            return dt.replace(tzinfo=timezone.utc)
        except:
            continue
    
    raise ValueError(f"無法解析日期: {date_str}")


def parse_episode_indices(episodes_str):
    """解析 episode 索引字符串，支援多種格式"""
    if not episodes_str:
        return []
    
    indices = []
    # 分割逗號分隔的值
    for part in episodes_str.split(','):
        part = part.strip()
        if '-' in part:
            # 處理範圍，如 "1-5"
            try:
                start, end = map(int, part.split('-'))
                indices.extend(range(start, end + 1))
            except ValueError:
                raise ValueError(f"無效的範圍格式: {part}")
        else:
            # 處理單個數字
            try:
                indices.append(int(part))
            except ValueError:
                raise ValueError(f"無效的episode索引: {part}")
    
    return sorted(list(set(indices)))  # 去重並排序


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='統一的Podcast處理腳本 - 增強轉錄版本')
    parser.add_argument('--podcast', '-p', type=str, help='指定podcast名稱')
    parser.add_argument('--episode', '-e', type=int, default=0, help='episode索引 (0=最新, 1=第二新...)')
    parser.add_argument('--episodes', type=str, help='處理多個episodes，支援格式: "1,3,5" 或 "1-5" 或 "1,3-5,7"')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有podcast')
    parser.add_argument('--list-episodes', action='store_true', help='列出指定podcast的所有episodes')
    parser.add_argument('--date-range', type=str, help='處理日期範圍內的episodes，格式: YYYY-MM-DD:YYYY-MM-DD')
    parser.add_argument('--start-date', type=str, help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='結束日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        processor = UnifiedPodcastProcessor()
        
        if args.list:
            print("📋 數據庫中的podcast:")
            podcasts = processor.get_podcasts_from_db()
            for i, podcast in enumerate(podcasts, 1):
                status = "🟢" if podcast['is_active'] else "🔴"
                print(f"  {i}. {status} {podcast['name']}")
                print(f"     📡 RSS Feed: {podcast['rss_url']}")
                if podcast.get('description'):
                    desc = podcast['description'][:100] + "..." if len(podcast['description']) > 100 else podcast['description']
                    print(f"     📝 描述: {desc}")
                print()
        
        elif args.list_episodes:
            if not args.podcast:
                print("❌ 請使用 --podcast 指定要列出的podcast")
                return
            
            # 解析日期範圍
            start_date = None
            end_date = None
            
            if args.date_range:
                # 格式: YYYY-MM-DD:YYYY-MM-DD
                try:
                    start_str, end_str = args.date_range.split(':')
                    start_date = parse_date_range(start_str)
                    end_date = parse_date_range(end_str)
                except:
                    print("❌ 日期範圍格式錯誤，應為: YYYY-MM-DD:YYYY-MM-DD")
                    return
            else:
                if args.start_date:
                    start_date = parse_date_range(args.start_date)
                if args.end_date:
                    end_date = parse_date_range(args.end_date)
            
            processor.list_episodes(args.podcast, start_date, end_date)
        
        elif args.episodes:
            if not args.podcast:
                print("❌ 請使用 --podcast 指定要處理的podcast")
                return
            
            try:
                episode_indices = parse_episode_indices(args.episodes)
                if not episode_indices:
                    print("❌ 未指定有效的episode索引")
                    return
                
                print(f"📋 將處理episodes: {episode_indices}")
                processor.process_multiple_episodes(args.podcast, episode_indices)
            except ValueError as e:
                print(f"❌ {e}")
                return
        
        elif args.date_range or args.start_date or args.end_date:
            if not args.podcast:
                print("❌ 請使用 --podcast 指定要處理的podcast")
                return
            
            # 解析日期範圍
            start_date = None
            end_date = None
            
            if args.date_range:
                try:
                    start_str, end_str = args.date_range.split(':')
                    start_date = parse_date_range(start_str)
                    end_date = parse_date_range(end_str)
                except:
                    print("❌ 日期範圍格式錯誤，應為: YYYY-MM-DD:YYYY-MM-DD")
                    return
            else:
                if args.start_date:
                    start_date = parse_date_range(args.start_date)
                if args.end_date:
                    end_date = parse_date_range(args.end_date)
            
            processor.process_date_range(args.podcast, start_date, end_date)
        
        else:
            processor.process_podcast_episode(args.podcast, args.episode)
            
    except KeyboardInterrupt:
        print("\n❌ 用戶取消操作")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")


if __name__ == "__main__":
    main()