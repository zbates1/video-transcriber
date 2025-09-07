# Project Architecture

This file defines the system structure, component interactions, and data flow for the video transcription pipeline.

## Directory Structure

```
video_transcriber/
├── src/
│   ├── models/          # Data models (VideoFile, Transcription, Summary)
│   ├── services/        # Core processing services
│   │   ├── audio_extractor.py    # Video to audio conversion
│   │   ├── transcriber.py        # Audio to text transcription
│   │   └── summarizer.py         # AI summary generation
│   ├── utils/           # Shared utilities and helpers
│   │   ├── file_handler.py       # File I/O operations
│   │   ├── config.py             # Configuration management
│   │   └── validators.py         # Input validation
│   └── main.py          # CLI entry point
├── tests/
│   ├── unit/            # Unit tests for individual components
│   └── integration/     # Integration tests for full pipeline
├── output/              # Generated transcription and summary files
└── requirements.txt     # Python dependencies
```

## Component Map

Pipeline flow showing component interactions:

- `main.py` → `utils/validators.py` → `models/VideoFile`
- `main.py` → `services/audio_extractor.py` → `utils/file_handler.py`
- `services/audio_extractor.py` → `services/transcriber.py` → `models/Transcription`
- `services/transcriber.py` → `services/summarizer.py` → `models/Summary`
- `services/summarizer.py` → `utils/file_handler.py` → output files

## Interface Definitions

### Service Interfaces

**AudioExtractor**
- `extract_audio(video_path: str) -> str`: Extract audio from video file, return audio path
- `cleanup_temp_files() -> None`: Clean up temporary audio files

**Transcriber**
- `transcribe(audio_path: str) -> str`: Convert audio to text transcription
- `set_language(language: str) -> None`: Set transcription language

**Summarizer**
- `generate_summary(text: str, api_key: str) -> str`: Generate AI summary using ChatGPT API
- `set_summary_length(length: str) -> None`: Set summary length (short/medium/long)

### Model Interfaces

**VideoFile**
- Properties: `path`, `filename`, `size`, `duration`
- Methods: `validate()`, `get_metadata()`

**Transcription**
- Properties: `text`, `confidence`, `language`, `timestamp`
- Methods: `save_to_file(path: str)`, `get_word_count()`

**Summary**
- Properties: `text`, `original_length`, `summary_length`, `timestamp`
- Methods: `save_to_file(path: str)`, `get_compression_ratio()`

## Data Flow

1. **Input Stage**
   - CLI receives .mp4 file path as argument
   - Validator checks file existence and format
   - VideoFile model created with metadata

2. **Processing Stage**
   - AudioExtractor converts video → temporary audio file
   - Transcriber processes audio → text transcription
   - Summarizer sends transcription to ChatGPT API → summary

3. **Output Stage**
   - Transcription saved to output/[filename]_transcription.txt
   - Summary saved to output/[filename]_summary.txt
   - Temporary audio files cleaned up
   - Success status returned to user

## Integration Points

- **File Handling**: All services must use FileHandler utility for consistent I/O
- **Error Handling**: All services must return standardized error responses
- **Configuration**: ChatGPT API key must be managed securely via Config utility
- **Pipeline Flow**: Video → Audio → Transcription → Summary (sequential processing)
- **Cleanup**: Temporary files must be properly managed and cleaned up

## Testing Requirements

- **Unit Tests**: Each service tested in isolation with mock dependencies
- **Integration Tests**: Full pipeline test with sample video file
- **Error Tests**: Handle invalid files, missing API keys, API failures
- **Performance Tests**: Test with various video lengths and formats