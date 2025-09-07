# Video Transcriber

Convert MP4 videos to text transcriptions with optional AI-generated summaries using OpenAI Whisper and ChatGPT.

## Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** - Required for audio extraction
   - **Windows**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - **Windows (recommended)**: 
   ```bash
   winget install ffmpeg
   ```
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

### Install Dependencies

```bash
git clone https://github.com/zbates1/video-transcriber.git
cd video_transcriber
pip install -r requirements.txt
```

## Usage

### Basic Transcription (No API Key Required)

```bash
python src/main.py path/to/video.mp4
```

### With AI Summary (Requires OpenAI API Key)

Set your API key (**recommended to setup OPENAI_API_KEY in *.env* file in root**):
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Then run:
```bash
python src/main.py path/to/video.mp4
```

Or pass the key directly:
```bash
python src/main.py path/to/video.mp4 --api-key "your-api-key-here"
```

### Advanced Options

```bash
# Custom output directory
python src/main.py video.mp4 --output-dir "transcripts/"

# Different language
python src/main.py video.mp4 --language "es"

# Verbose output
python src/main.py video.mp4 --verbose
```

### Output Files

- `{video_name}_transcription.txt` - Full transcription
- `{video_name}_summary.txt` - AI summary (if API key provided)

## Getting an OpenAI API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)