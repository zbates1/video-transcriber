# Output Directory

This directory contains generated files from the video transcription pipeline.

## Directory Structure

- **transcriptions/** - Contains individual transcription files (.txt)
- **summaries/** - Contains AI-generated summary files (.txt) 
- **archives/** - Contains archived results organized by date

## File Naming Convention

The pipeline generates files using the following naming pattern:

- Transcriptions: `{video_filename}_transcription.txt`
- Summaries: `{video_filename}_summary.txt`

## Example

For a video file named `meeting_recording.mp4`, the pipeline will generate:

- `output/meeting_recording_transcription.txt` - Full text transcription
- `output/meeting_recording_summary.txt` - AI-generated summary (if API key provided)

## Directory Management

- Files are automatically saved to this directory when the pipeline runs
- The main CLI allows specifying a custom output directory with `--output-dir`
- Old files are not automatically overwritten - they will be replaced if the same filename is processed again

## Permissions

Ensure this directory is writable by the application. The pipeline will validate directory permissions before processing.