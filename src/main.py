#!/usr/bin/env python3
"""
Main CLI entry point for the video transcriber pipeline.

This script orchestrates the full video transcription pipeline:
Video → Audio → Transcription → Summary
"""

import argparse
import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.validators import validate_video_file, validate_output_directory, validate_api_key, ValidationError
from src.utils.config import Config
from src.utils.file_handler import FileHandler
from src.models.video_file import VideoFile
from src.services.audio_extractor import AudioExtractor
from src.services.transcriber import Transcriber
from src.services.summarizer import Summarizer


class VideoTranscriberCLI:
    """Main CLI orchestrator for the video transcription pipeline."""
    
    def __init__(self):
        self.config = Config()
        self.file_handler = FileHandler()
        
        # Initialize services
        self.audio_extractor = AudioExtractor()
        self.transcriber = Transcriber()
        self.summarizer = Summarizer()
    
    def run(self, video_path: str, output_dir: str = "output", api_key: str = None) -> dict:
        """
        Run the complete video transcription pipeline.
        
        Args:
            video_path: Path to input video file
            output_dir: Directory to save outputs (default: "output")
            api_key: ChatGPT API key for summary generation
            
        Returns:
            Dictionary with results and file paths
        """
        try:
            # Step 1: Validate inputs
            print(f"🎥 Processing video: {video_path}")
            
            # Validate video file
            is_valid, error_msg = validate_video_file(video_path)
            if not is_valid:
                raise ValidationError(f"Invalid video file: {error_msg}")
            
            # Validate output directory
            validate_output_directory(output_dir)
            
            # Create VideoFile model
            video_file = VideoFile(video_path)
            video_file.validate()
            
            print(f"✅ Video file validated: {video_file.filename}")
            
            # Step 2: Extract audio from video
            print("🎵 Extracting audio from video...")
            try:
                audio_path = self.audio_extractor.extract_audio(video_path)
                print(f"✅ Audio extracted: {audio_path}")
            except Exception as e:
                raise RuntimeError(f"Audio extraction failed: {str(e)}")
            
            # Step 3: Transcribe audio to text
            print("📝 Transcribing audio to text...")
            try:
                transcription = self.transcriber.transcribe_to_model(audio_path)
                print(f"✅ Transcription completed: {transcription.get_word_count()} words")
                
                # Save transcription
                base_name = Path(video_file.filename).stem
                transcription_path = os.path.join(output_dir, f"{base_name}_transcription.txt")
                transcription.save_to_file(transcription_path)
                print(f"💾 Transcription saved: {transcription_path}")
                
            except Exception as e:
                raise RuntimeError(f"Transcription failed: {str(e)}")
            
            finally:
                # Clean up temporary audio file
                try:
                    self.audio_extractor.cleanup_temp_files()
                    print("🧹 Temporary audio files cleaned up")
                except Exception as e:
                    print(f"⚠️ Warning: Failed to clean up temporary files: {str(e)}")
            
            # Step 4: Generate AI summary (if API key provided)
            summary_path = None
            if api_key:
                try:
                    validate_api_key(api_key)
                    
                    print("🤖 Generating AI summary...")
                    summary_text = self.summarizer.generate_summary(transcription.text, api_key)
                    if summary_text:
                        summary = self.summarizer.create_summary_object(transcription.text, summary_text)
                        print(f"✅ Summary generated: {summary.get_compression_ratio():.1%} compression")
                    else:
                        raise RuntimeError("Summary generation returned empty result")
                    
                    # Save summary
                    summary_path = os.path.join(output_dir, f"{base_name}_summary.txt")
                    summary.save_to_file(summary_path)
                    print(f"💾 Summary saved: {summary_path}")
                    
                except Exception as e:
                    print(f"⚠️ Warning: Summary generation failed: {str(e)}")
                    print("📝 Continuing with transcription only...")
            else:
                print("ℹ️ No API key provided. Skipping summary generation.")
                print("  Use --api-key option or set OPENAI_API_KEY environment variable.")
            
            # Step 5: Return results
            results = {
                "video_file": video_path,
                "transcription_file": transcription_path,
                "transcription_word_count": transcription.get_word_count(),
                "transcription_confidence": transcription.confidence,
                "summary_file": summary_path,
                "output_directory": output_dir,
                "success": True
            }
            
            print(f"\n🎉 Pipeline completed successfully!")
            print(f"📁 Output directory: {output_dir}")
            print(f"📄 Transcription: {transcription_path}")
            if summary_path:
                print(f"📄 Summary: {summary_path}")
            
            return results
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {str(e)}")
            return {
                "video_file": video_path,
                "error": str(e),
                "success": False
            }
    
    def parse_arguments(self):
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description="Convert MP4 videos to text transcriptions with AI-generated summaries",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python src/main.py video.mp4
  python src/main.py video.mp4 --output-dir transcripts/
  python src/main.py video.mp4 --api-key sk-xxx --output-dir results/
  python src/main.py video.mp4 --language es-ES
            """
        )
        
        parser.add_argument(
            "video_path",
            help="Path to the input MP4 video file"
        )
        
        parser.add_argument(
            "--output-dir", "-o",
            default="output",
            help="Directory to save transcription and summary files (default: output)"
        )
        
        parser.add_argument(
            "--api-key", "-k",
            default=None,
            help="ChatGPT API key for summary generation (or set OPENAI_API_KEY env var)"
        )
        
        parser.add_argument(
            "--language", "-l",
            default="en-US",
            help="Language for speech recognition (default: en-US)"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )
        
        return parser.parse_args()


def main():
    """Main entry point."""
    cli = VideoTranscriberCLI()
    args = cli.parse_arguments()
    
    # Get API key from argument or environment
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    
    # Set transcriber language
    cli.transcriber.set_language(args.language)
    
    # Run pipeline
    results = cli.run(
        video_path=args.video_path,
        output_dir=args.output_dir,
        api_key=api_key
    )
    
    # Exit with appropriate code
    if results["success"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()