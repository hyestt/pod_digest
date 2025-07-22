# Unified Podcast Processor 使用指南

## 概述
`unified_podcast_processor.py` 是一個獨立的腳本，用於下載、轉錄和摘要 podcast 節目。支援多個 podcast 源，包括 Acquired、The Journal 和 Planet Money。

## 新功能 (Enhanced 版本)
增強版 `unified_podcast_processor_enhanced.py` 新增以下功能：
1. **列出所有 episodes 及標題**：可以查看某個 podcast 的所有集數列表
2. **日期區間篩選**：支援處理特定日期範圍內的節目（開發中）

## 前置需求

### 1. 必要的環境變數
```bash
export OPENAI_API_KEY="你的-openai-api-key"
```

### 2. Python 依賴套件
```bash
pip install feedparser httpx openai
```

### 3. 可選依賴（音頻分割功能）
如果要處理超過 25MB 的音頻檔案，建議安裝：
```bash
pip install pydub
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

## 基本使用方法

### 1. 查看支援的 podcast
```bash
python3 unified_podcast_processor.py --list
```

輸出範例：
```
📋 數據庫中的podcast:
  1. 🟢 Acquired
  2. 🟢 The Journal.
  3. 🟢 Planet Money
```

### 2. 處理最新一集
```bash
# 處理 Planet Money 最新一集
python3 unified_podcast_processor.py --podcast "Planet Money" --episode 0

# 處理 Acquired 最新一集
python3 unified_podcast_processor.py --podcast "Acquired" --episode 0
```

### 3. 處理特定集數
```bash
# 處理 Planet Money 第二新的一集（索引從 0 開始）
python3 unified_podcast_processor.py --podcast "Planet Money" --episode 1
```

### 4. 查看目錄結構
```bash
python3 unified_podcast_processor.py --list-dirs
```

### 5. 清理特定 podcast 的檔案
```bash
python3 unified_podcast_processor.py --cleanup "Planet Money"
```

## 增強版功能使用

### 1. 僅轉錄版本（無摘要）
最新的 `unified_podcast_processor_transcript_enhanced.py` 只做轉錄，不生成摘要：
```bash
# 處理最新一集（只轉錄）
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --episode 0
```

### 2. 列出所有 episodes 及標題
```bash
# 列出 Planet Money 的所有集數
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --list-episodes

# 列出特定日期範圍的集數
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --list-episodes --start-date "2025-07-05" --end-date "2025-07-09"
```

輸出範例：
```
📋 Planet Money Episode列表
📅 日期範圍: 2025-07-05 到 2025-07-09
📊 總共: 1 集

  0. [2025-07-09] Summer School 1: A government's role in the economy is to make us all richer [2146]
```

### 3. 處理特定集數的 episodes
```bash
# 處理單個集數
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --episode 5

# 處理多個特定集數
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --episodes "1,3,5"

# 處理集數範圍
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --episodes "1-5"

# 混合格式
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --episodes "1,3-5,7"
```

### 4. 處理日期區間內的 episodes
```bash
# 處理 2025 年 7 月 5 日到 7 月 9 日的所有集數
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --date-range "2025-07-05:2025-07-09"

# 或使用單獨的開始/結束日期
python3 unified_podcast_processor_transcript_enhanced.py --podcast "Planet Money" --start-date "2025-07-05" --end-date "2025-07-09"
```

注意：日期格式支援：
- YYYY-MM-DD (推薦)
- MM/DD/YYYY
- YYYY/MM/DD

## 輸出檔案結構

處理完成後，檔案會儲存在以下結構中：

```
downloads/
├── audio/                           # 音頻檔案（處理後會自動刪除）
├── transcripts/                     # 轉錄文字
│   └── Planet Money/
│       └── 2025-07-18_Planet Money/
│           └── english/
│               └── Why are we so obsessed with manufacturing__2217_transcript.txt
└── summaries/                       # 摘要
    └── Planet Money/
        └── 2025-07-18_Planet Money/
            ├── english/
            │   └── Why are we so obsessed with manufacturing__2218_summary.txt
            └── chinese/
                └── Why are we so obsessed with manufacturing__2218_summary.txt
```

## 處理流程

1. **下載音頻**：從 RSS feed 下載最新的音頻檔案
2. **檔案大小檢查**：如果超過 24MB，會自動分割
3. **Whisper 轉錄**：使用 OpenAI Whisper API 轉錄音頻
4. **生成摘要**：使用 GPT-4 生成英文和中文摘要
5. **儲存結果**：轉錄和摘要分別儲存到對應目錄
6. **清理**：自動刪除臨時音頻檔案

## 常見問題

### 1. API 額度不足
錯誤訊息：`insufficient_quota`
解決方案：充值 OpenAI 帳戶或更換有額度的 API key

### 2. 音頻分割功能不可用
如果看到「音頻切割功能不可用」的提示，腳本會使用二進制分割作為備用方案。這可能在音頻邊界處產生輕微失真，但通常不影響轉錄結果。

### 3. 處理時間
- 下載：取決於網路速度，通常 5-10 秒
- 轉錄：約 1-2 分鐘（取決於音頻長度）
- 摘要生成：約 1 分鐘
- 總時間：通常 2-4 分鐘完成整個流程

## 批次處理範例

如果需要批次處理多集，可以使用 shell 腳本：

```bash
#!/bin/bash
# 處理 Planet Money 最新 5 集
for i in {0..4}; do
    echo "處理第 $i 集..."
    python3 unified_podcast_processor.py --podcast "Planet Money" --episode $i
    sleep 5  # 避免 API 請求過於頻繁
done
```

## 成本估算

- Whisper API：$0.006/分鐘
- GPT-4 摘要：約 $0.05-0.10/集
- 平均每集總成本：約 $0.15-0.25

## 注意事項

1. **API Key 安全**：不要將 API key 提交到版本控制系統
2. **處理大檔案**：超過 25MB 的音頻會自動分割，但可能影響轉錄品質
3. **網路穩定性**：確保網路連線穩定，避免下載中斷
4. **儲存空間**：每集約產生 50-100KB 的文字檔案

## 進階用法

如果需要修改處理邏輯，可以直接編輯 `unified_podcast_processor.py`：
- 修改摘要提示詞：搜尋 `summarize_transcript` 方法
- 調整檔案分割大小：修改 `MAX_FILE_SIZE_MB` 變數
- 添加新的 podcast：在資料庫中新增 RSS feed URL