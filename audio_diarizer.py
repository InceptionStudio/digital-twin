import os
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import torch
import torchaudio
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pydub import AudioSegment
from config import Config

# Optional import for simple_diarizer
try:
    from simple_diarizer.diarizer import Diarizer
    SIMPLE_DIARIZER_AVAILABLE = True
except ImportError:
    SIMPLE_DIARIZER_AVAILABLE = False

class AudioDiarizer:
    def __init__(self, diarizer_type: str = "pyannote", use_gpu: bool = False, 
                 embed_model: str = "xvec", cluster_method: str = "sc"):
        """
        Initialize the audio diarizer with specified backend.
        
        Args:
            diarizer_type: Type of diarizer ("pyannote" or "simple")
            use_gpu: Whether to use GPU for processing
            embed_model: Embedding model for simple_diarizer ("xvec" or "ecapa")
            cluster_method: Clustering method for simple_diarizer ("ahc" or "sc")
        """
        self.diarizer_type = diarizer_type
        
        if diarizer_type == "pyannote":
            # Initialize pyannote.audio pipeline for speaker diarization
            self.hf_token = Config.HUGGINGFACE_TOKEN
            if not self.hf_token:
                raise ValueError("HuggingFace token not found in configuration. Please set HUGGINGFACE_TOKEN in your .env file")
            
            print("🤖 Loading pyannote.audio speaker diarization pipeline...")
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )
            
            # Send to GPU if available and requested
            if use_gpu and torch.cuda.is_available():
                self.diarization_pipeline.to(torch.device("cuda"))
                print("🚀 Using GPU for diarization")
            else:
                print("💻 Using CPU for diarization")
                
        elif diarizer_type == "simple":
            if not SIMPLE_DIARIZER_AVAILABLE:
                raise ImportError("simple_diarizer not available. Install with: pip install simple-diarizer")
            
            print(f"🤖 Loading simple_diarizer with {embed_model} embedding and {cluster_method} clustering...")
            self.simple_diarizer = Diarizer(
                embed_model=embed_model,
                cluster_method=cluster_method
            )
            print("💻 Using CPU for diarization (simple_diarizer)")
            
        else:
            raise ValueError(f"Unsupported diarizer type: {diarizer_type}. Use 'pyannote' or 'simple'")
    
    def perform_diarization(self, audio_path: str, num_speakers: Optional[int] = None, 
                           threshold: Optional[float] = None) -> Any:
        """
        Perform speaker diarization using the selected backend.
        
        Args:
            audio_path: Path to the audio file
            num_speakers: Number of speakers (for simple_diarizer)
            threshold: Threshold for clustering (for simple_diarizer)
        
        Returns:
            Diarization result with speaker segments
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            print(f"🎭 Performing speaker diarization: {audio_path}")
            start_time = time.time()
            
            if self.diarizer_type == "pyannote":
                # Load audio into memory for faster processing
                print("📥 Loading audio into memory...")
                waveform, sample_rate = torchaudio.load(audio_path)
                
                # Apply pretrained pipeline with progress hook using memory data
                with ProgressHook() as hook:
                    diarization = self.diarization_pipeline(
                        {"waveform": waveform, "sample_rate": sample_rate}, 
                        hook=hook
                    )
                    
            elif self.diarizer_type == "simple":
                # Use simple_diarizer
                print("📥 Processing with simple_diarizer...")
                if num_speakers is not None:
                    diarization = self.simple_diarizer.diarize(audio_path, num_speakers=num_speakers)
                elif threshold is not None:
                    diarization = self.simple_diarizer.diarize(audio_path, threshold=threshold)
                else:
                    # Default to 2 speakers if neither is specified
                    diarization = self.simple_diarizer.diarize(audio_path, num_speakers=2)
            
            end_time = time.time()
            print(f"✅ Diarization completed in {end_time - start_time:.2f}s")
            
            return diarization
            
        except Exception as e:
            raise Exception(f"Failed to perform diarization: {str(e)}")
    
    def transcribe_with_diarization(self, audio_path: str, num_speakers: Optional[int] = None, 
                                   threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Perform speaker diarization using the selected backend.
        
        Args:
            audio_path: Path to the audio file
            num_speakers: Number of speakers (for simple_diarizer)
            threshold: Threshold for clustering (for simple_diarizer)
        
        Returns:
            Diarization result with speaker segments
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            print(f"🎤 Processing audio: {audio_path}")
            start_time = time.time()
            
            # Perform speaker diarization
            diarization = self.perform_diarization(audio_path, num_speakers, threshold)
            
            end_time = time.time()
            print(f"✅ Diarization completed in {end_time - start_time:.2f}s")
            
            return {
                "diarization": diarization
            }
            
        except Exception as e:
            raise Exception(f"Failed to process audio: {str(e)}")
    
    def extract_speaker_segments(self, transcription) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract and organize segments by speaker using the selected diarization backend.
        
        Args:
            transcription: Diarization result
        
        Returns:
            Dictionary with speaker IDs as keys and lists of segments as values
        """
        diarization = transcription.get("diarization")
        
        if not diarization:
            return {}
        
        speakers = {}
        
        if self.diarizer_type == "pyannote":
            # Get diarization results and organize by speaker
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if speaker not in speakers:
                    speakers[speaker] = []
                
                speakers[speaker].append({
                    "start": turn.start,
                    "end": turn.end,
                    "text": "",  # No transcription text available
                    "timestamp": [turn.start, turn.end]
                })
                
        elif self.diarizer_type == "simple":
            # Process simple_diarizer segments
            for segment in diarization:
                speaker = f"SPEAKER_{segment['label']}"
                if speaker not in speakers:
                    speakers[speaker] = []
                
                speakers[speaker].append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": "",  # No transcription text available
                    "timestamp": [segment["start"], segment["end"]]
                })
        
        return speakers
    
    def create_speaker_audio(self, audio_path: str, speaker_segments: List[Dict[str, Any]], 
                           speaker_id: str, output_dir: Path) -> str:
        """
        Create audio file for a specific speaker by stitching together their segments.
        
        Args:
            audio_path: Path to the original audio file
            speaker_segments: List of segments for this speaker
            speaker_id: Speaker identifier
            output_dir: Directory to save the output audio
        
        Returns:
            Path to the generated speaker audio file
        """
        try:
            print(f"🎵 Creating audio for speaker {speaker_id}...")
            
            # Load the original audio
            audio = AudioSegment.from_file(audio_path)
            
            # Create empty audio segment for this speaker
            speaker_audio = AudioSegment.empty()
            
            # Add each segment for this speaker
            for segment in speaker_segments:
                start_ms = int(segment["start"] * 1000)
                end_ms = int(segment["end"] * 1000)
                
                # Extract the segment from the original audio
                segment_audio = audio[start_ms:end_ms]
                
                # Add to speaker audio
                speaker_audio += segment_audio
            
            # Save the speaker audio
            output_filename = f"speaker_{speaker_id}_{int(time.time())}.mp3"
            output_path = output_dir / output_filename
            
            speaker_audio.export(str(output_path), format="mp3")
            
            print(f"✅ Speaker {speaker_id} audio saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise Exception(f"Failed to create audio for speaker {speaker_id}: {str(e)}")
    
    def process_audio(self, audio_path: str, output_dir: Optional[str] = None, 
                     num_speakers: Optional[int] = None, threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Process audio file to separate speakers.
        
        Args:
            audio_path: Path to the audio file
            output_dir: Optional output directory (defaults to Config.OUTPUT_DIR)
        
        Returns:
            Dictionary with processing results
        """
        if output_dir is None:
            output_dir = Config.OUTPUT_DIR
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Transcribe with diarization
        transcription = self.transcribe_with_diarization(audio_path, num_speakers, threshold)
        
        # Step 2: Extract speaker segments
        speakers = self.extract_speaker_segments(transcription)
        
        print(f"🎭 Found {len(speakers)} speakers in the audio")
        
        # Step 3: Create individual audio files for each speaker
        speaker_audio_files = {}
        speaker_transcripts = {}
        
        for speaker_id, segments in speakers.items():
            print(f"\n📝 Speaker {speaker_id}:")
            print(f"   Segments: {len(segments)}")
            
            # Create transcript for this speaker
            transcript = " ".join([seg["text"] for seg in segments])
            speaker_transcripts[speaker_id] = transcript
            
            print(f"   Transcript: {transcript[:100]}{'...' if len(transcript) > 100 else ''}")
            
            # Create audio file for this speaker
            audio_file = self.create_speaker_audio(audio_path, segments, speaker_id, output_dir)
            speaker_audio_files[speaker_id] = audio_file
        
        # Save transcripts to JSON file
        transcript_file = output_dir / f"transcripts_{int(time.time())}.json"
        with open(transcript_file, 'w') as f:
            json.dump({
                "original_audio": audio_path,
                "speakers": speaker_transcripts,
                "segments": speakers,
                "audio_files": speaker_audio_files
            }, f, indent=2)
        
        print(f"\n📄 Transcripts saved: {transcript_file}")
        
        return {
            "speakers": len(speakers),
            "audio_files": speaker_audio_files,
            "transcripts": speaker_transcripts,
            "transcript_file": str(transcript_file)
        }
    
    def test_diarization(self) -> bool:
        """Test the selected diarization functionality with DiaTest.mp3."""
        try:
            test_file = "DiaTest.mp3"
            if not Path(test_file).exists():
                print(f"❌ Test file not found: {test_file}")
                return False
            
            print(f"🧪 Testing with file: {test_file}")
            
            # Test diarization
            transcription = self.transcribe_with_diarization(test_file)
            
            # Test speaker extraction
            speakers = self.extract_speaker_segments(transcription)
            
            print(f"✅ Test successful! Found {len(speakers)} speakers")
            for speaker_id, segments in speakers.items():
                total_duration = sum(seg["end"] - seg["start"] for seg in segments)
                print(f"   Speaker {speaker_id}: {len(segments)} segments ({total_duration:.1f}s)")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Audio Diarization Tool using pyannote.audio or simple_diarizer")
    parser.add_argument("audio_file", nargs="?", help="Path to the audio file to process")
    parser.add_argument("-o", "--output", help="Output directory (defaults to config OUTPUT_DIR)")
    parser.add_argument("--test", action="store_true", help="Test diarization functionality")
    parser.add_argument("--diarizer", choices=["pyannote", "simple"], default="pyannote", 
                       help="Diarization backend to use (default: pyannote)")
    parser.add_argument("--embed-model", choices=["xvec", "ecapa"], default="xvec",
                       help="Embedding model for simple_diarizer (default: xvec)")
    parser.add_argument("--cluster-method", choices=["ahc", "sc"], default="sc",
                       help="Clustering method for simple_diarizer (default: sc)")
    parser.add_argument("--num-speakers", type=int, help="Number of speakers (for simple_diarizer)")
    parser.add_argument("--threshold", type=float, help="Threshold for clustering (for simple_diarizer)")
    parser.add_argument("--gpu", action="store_true", help="Use GPU for processing (pyannote only)")
    
    args = parser.parse_args()
    
    # If --test is used, we don't need audio_file
    if args.test:
        args.audio_file = None
    elif not args.audio_file:
        parser.error("audio_file is required unless --test is specified")
    
    try:
        diarizer = AudioDiarizer(
            diarizer_type=args.diarizer,
            use_gpu=args.gpu,
            embed_model=args.embed_model,
            cluster_method=args.cluster_method
        )
        
        if args.test:
            print("🔧 Testing diarization functionality...")
            if diarizer.test_diarization():
                print("✅ Diarization test successful")
            else:
                print("❌ Diarization test failed")
            return
        
        print("🎤 Audio Diarization Tool")
        print("=" * 50)
        
        # Process the audio file
        result = diarizer.process_audio(args.audio_file, args.output, args.num_speakers, args.threshold)
        
        print("\n🎉 Processing completed!")
        print("=" * 50)
        print(f"📊 Speakers detected: {result['speakers']}")
        print(f"🎵 Audio files generated: {len(result['audio_files'])}")
        print(f"📄 Transcript file: {result['transcript_file']}")
        
        print("\n📁 Generated files:")
        for speaker_id, audio_file in result['audio_files'].items():
            print(f"   Speaker {speaker_id}: {audio_file}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
