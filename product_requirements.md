# Product Requirements

## 1. Project Vision & Goal

To build a simple CLI pipeline that takes MP4 video files and automatically converts them to text transcriptions with AI-generated summaries.

## 2. Key Features & User Stories

- **As a user, I want to** provide a .mp4 file as input via command line
- **As a user, I want to** extract audio from the video file automatically
- **As a user, I want to** convert the audio to text transcription using speech-to-text
- **As a user, I want to** generate an AI summary of the transcription using ChatGPT API
- **As a user, I want to** receive both the full transcription and summary as output files

## 3. Non-Functional Requirements

- The system must be written in Python 3.8+
- CLI interface should be simple and intuitive
- Must handle common video formats (.mp4 initially)
- Requires ChatGPT API key for summary generation
- Output files should be in text format (.txt)
- Include error handling for invalid files and API failures
- Code must be well-documented with type hints
