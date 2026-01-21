import torch
import gc
import re
import os
import warnings
import shutil
from datetime import datetime
from transformers import T5Tokenizer, T5ForConditionalGeneration
try:
    import whisper
except Exception as e:
    whisper = None
    _whisper_import_error = e

# Filter warnings
warnings.filterwarnings('ignore')

# Monkeypatch torchaudio.set_audio_backend for compatibility with newer torchaudio versions
import torchaudio
if not hasattr(torchaudio, 'set_audio_backend'):
    torchaudio.set_audio_backend = lambda backend: None

try:
    from pyannote.audio import Pipeline
except ImportError:
    Pipeline = None
    print("⚠️ Pyannote Audio not installed. Diarization will be disabled.")
import config
from datetime import timedelta

class SmartT5LargeDocumentGenerator:
    """
    Intelligent T5-based document generator with Flan-T5-Large.
    Complete pipeline: Audio -> T5-Large Summary -> Professional Documents
    Updated model: google/flan-t5-large for superior summarization quality
    Adapted from the notebook to work within the backend application.
    """
    
    def __init__(self, whisper_model="base", t5_model="google/flan-t5-large"):
        """
        Initialize with T5-Large and Whisper models
        Uses the larger Flan-T5-Large model for better summarization
        """
        # Clear memory
        torch.cuda.empty_cache()
        gc.collect()

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Device: {self.device}")
        
        if self.device == "cuda":
            print(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
            print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            print("⚠️ WARNING: Running on CPU. switched to 'base' models for performance.")
        
        # Validate Whisper availability
        if whisper is None:
            raise ImportError(
                "Missing Python package 'whisper' (OpenAI Whisper).\n"
                "Install dependencies in the 'python-backend' folder with:\n"
                "  python -m pip install -r requirements.txt\n"
                "Also ensure `ffmpeg` is installed and available on PATH (required by Whisper)."
            )

        # Validate ffmpeg availability (Whisper depends on ffmpeg for audio processing)
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            raise EnvironmentError(
                "Missing system dependency 'ffmpeg'. OpenAI Whisper requires ffmpeg to be installed and available on PATH.\n"
                "On Windows you can install with: `winget install --id Gyan.FFmpeg -e` or install via Chocolatey: `choco install ffmpeg -y`.\n"
                "After installing, restart your terminal/IDE so the PATH changes take effect, then restart this server."
            )

        # Load Whisper
        print(f"\n📥 Loading Whisper '{whisper_model}'...")
        self.whisper_model = whisper.load_model(whisper_model, device=self.device)
        print("✅ Whisper loaded!")
        
        # Load T5
        print(f"\\n📥 Loading T5 '{t5_model}'...")
        self.tokenizer = T5Tokenizer.from_pretrained(t5_model, legacy=False)

        dtype = torch.float16 if self.device == "cuda" else torch.float32
        # Use device_map="auto" if available and on cuda for better memory management, 
        # but manual to() seems reliable in notebook code.
        self.model = T5ForConditionalGeneration.from_pretrained(
            t5_model,
            torch_dtype=dtype
        ).to(self.device)
        print("✅ T5 loaded!")
        
        # Load Diarization Pipeline
        self.diarization_pipeline = None
        if config.HUGGINGFACE_TOKEN and Pipeline:
            try:
                print(f"\\n📥 Loading Pyannote Pipeline...")
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=config.HUGGINGFACE_TOKEN
                )
                if self.device == "cuda":
                    self.diarization_pipeline.to(torch.device("cuda"))
                print("✅ Pyannote Pipeline loaded!")
            except Exception as e:
                print(f"⚠️ Failed to load Pyannote Pipeline: {e}")
        else:
            print("⚠️ Diarization disabled: Missing HUGGINGFACE_TOKEN or pyannote.audio")

        print("\\n" + "="*70)
        print("✨ Smart T5 Document Generator Ready!")
        print("="*70 + "\\n")


    def diarize_audio(self, audio_path, min_speakers=None, max_speakers=None):
        """
        Perform speaker diarization using Pyannote
        """
        if not self.diarization_pipeline:
            print("⚠️ Diarization pipeline not available")
            return []

        try:
            print(f"⏳ Running speaker diarization on {os.path.basename(audio_path)}...")
            diarization = self.diarization_pipeline(
                audio_path,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )

            speaker_segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })

            num_speakers = len(set([s["speaker"] for s in speaker_segments]))
            print(f"✅ Diarization complete! Detected {num_speakers} speakers")
            return speaker_segments

        except Exception as e:
            print(f"❌ Diarization error: {e}")
            return []

    def merge_transcription_with_diarization(self, transcription_segments, speaker_segments):
        """
        Merge Whisper timestamps with Pyannote speaker segments
        """
        if not speaker_segments:
            return transcription_segments

        merged_segments = []
        
        # If whisper segments don't have start/end, we can't merge properly
        # Assuming transcription_segments is list of dicts with start, end, text
        
        for w_seg in transcription_segments:
            # Whisper segment might look like: {'id': 0, 'seek': 0, 'start': 0.0, 'end': 7.0, 'text': '...', ...}
            seg_start = w_seg.get('start', 0)
            seg_end = w_seg.get('end', 0)
            text = w_seg.get('text', '').strip()
            
            if not text:
                continue

            assigned_speaker = "UNKNOWN"
            max_overlap = 0

            for p_seg in speaker_segments:
                # Calculate overlap
                overlap_start = max(seg_start, p_seg['start'])
                overlap_end = min(seg_end, p_seg['end'])
                overlap = max(0, overlap_end - overlap_start)

                if overlap > max_overlap:
                    max_overlap = overlap
                    assigned_speaker = p_seg['speaker']
            
            # Create a new merged segment object
            merged_segments.append({
                'start': seg_start,
                'end': seg_end,
                'text': text,
                'speaker': assigned_speaker
            })

        # Remap speaker labels (SPEAKER_00 -> Speaker 1)
        speaker_counts = {}
        for seg in merged_segments:
            spk = seg['speaker']
            speaker_counts[spk] = speaker_counts.get(spk, 0) + 1
        
        sorted_speakers = sorted(speaker_counts.items(), key=lambda x: x[1], reverse=True)
        speaker_map = {}
        for i, (spk, _) in enumerate(sorted_speakers, 1):
            speaker_map[spk] = f"Speaker {i}"
            
        for seg in merged_segments:
            seg['speaker'] = speaker_map.get(seg['speaker'], "Speaker ?")
            
        return merged_segments

    def format_transcript_with_speakers(self, merged_segments):
        """
        Format merged segments into a readable transcript string
        """
        lines = []
        current_speaker = None
        current_text = []

        for seg in merged_segments:
            speaker = seg['speaker']
            text = seg['text']

            if speaker != current_speaker:
                if current_speaker:
                    lines.append(f"{current_speaker}: {' '.join(current_text)}")
                current_speaker = speaker
                current_text = [text]
            else:
                current_text.append(text)
        
        # Append last one
        if current_speaker:
            lines.append(f"{current_speaker}: {' '.join(current_text)}")

        return "\n\n".join(lines)

    def transcribe_audio(self, audio_path):
        """Transcribe multilingual audio to English using Whisper"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"❌ File not found: {audio_path}")
        
        file_size = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"🎵 Audio: {os.path.basename(audio_path)} ({file_size:.2f} MB)")
        print(f"⏳ Transcribing with Whisper...")
        
        result = self.whisper_model.transcribe(
            audio_path,
            task='translate',
            language=None,
            fp16=self.device == "cuda",
            verbose=False,
            beam_size=5,
            best_of=5,
            temperature=0.0
        )
        
        # If verbose=True in transcribe, it returns segments. We need them for diarization.
        # But here we used verbose=False. Let's rely on result['segments'] which is usually present.
        segments = result.get('segments', [])
        
        lang_map = {
            'hi': 'Hindi (हिन्दी)',
            'en': 'English',
            'mr': 'Marathi (मराठी)'
        }
        
        detected = result.get('language', 'unknown')
        text = result['text'].strip()
        word_count = len(text.split())
        
        print(f"✅ Transcription complete!")
        print(f"🌍 Language: {lang_map.get(detected, detected)}")
        print(f"📝 Words: {word_count}")
        
        print(f"📝 Words: {word_count}")
        
        return {
            'text': text,
            'segments': segments,
            'language': detected,
            'language_name': lang_map.get(detected, detected),
            'word_count': word_count
        }

    def calculate_adaptive_summary_length(self, word_count, strategy):
        """
        Intelligent adaptive summary length calculation
        """
        # T5-optimized strategies
        strategies = {
            'ultra_concise': {'base_ratio': 0.12, 'min_words': 12, 'max_words': 60, 'description': 'Single sentence summaries'},
            'concise': {'base_ratio': 0.20, 'min_words': 20, 'max_words': 100, 'description': 'Brief, punchy summaries'},
            'balanced': {'base_ratio': 0.30, 'min_words': 30, 'max_words': 180, 'description': 'Balanced detail and brevity'},
            'detailed': {'base_ratio': 0.45, 'min_words': 50, 'max_words': 300, 'description': 'Comprehensive coverage'},
            'comprehensive': {'base_ratio': 0.60, 'min_words': 80, 'max_words': 450, 'description': 'Extensive detail'},
            'hybrid': {'base_ratio': 0.525, 'min_words': 65, 'max_words': 375, 'description': 'Hybrid: detailed + comprehensive'}
        }
        
        config = strategies.get(strategy, strategies['balanced']) # Default to balanced if unknown
        
        # Adaptive calculation based on input length
        if word_count < 40:
            max_words = max(config['min_words'], int(word_count * 0.85))
            min_words = max(8, int(word_count * 0.5))
            ratio = 0.85
        elif word_count < 120:
            max_words = max(config['min_words'], int(word_count * 0.65))
            min_words = max(12, int(word_count * 0.35))
            ratio = 0.65
        elif word_count < 250:
            max_words = int(word_count * 0.50)
            min_words = int(word_count * 0.25)
            ratio = 0.50
        elif word_count < 600:
            max_words = int(word_count * config['base_ratio'])
            min_words = int(word_count * (config['base_ratio'] * 0.45))
            ratio = config['base_ratio']
        elif word_count < 1500:
            max_words = int(word_count * (config['base_ratio'] * 0.95))
            min_words = int(word_count * (config['base_ratio'] * 0.40))
            ratio = config['base_ratio'] * 0.95
        elif word_count < 4000:
            max_words = int(word_count * (config['base_ratio'] * 0.85))
            min_words = int(word_count * (config['base_ratio'] * 0.35))
            ratio = config['base_ratio'] * 0.85
        else:
            max_words = int(word_count * (config['base_ratio'] * 0.75))
            min_words = int(word_count * (config['base_ratio'] * 0.30))
            ratio = config['base_ratio'] * 0.75
        
        max_words = min(max_words, config['max_words'])
        max_words = max(max_words, config['min_words'])
        min_words = min(min_words, max_words - 8)
        min_words = max(min_words, 8)
        
        max_tokens = int(max_words * 1.5)
        min_tokens = int(min_words * 1.5)
        
        return {
            'max_length': max_tokens,
            'min_length': min_tokens,
            'max_words': max_words,
            'min_words': min_words,
            'ratio': ratio,
            'strategy': strategy,
            'description': config['description']
        }

    def generate_t5_summary(self, text, max_length=512, min_length=100, quality='medium', custom_instruction=None):
        """
        Generate abstractive summary using T5
        """
        beam_config = {'fast': 2, 'medium': 4, 'high': 6, 'best': 10}
        num_beams = beam_config.get(quality, 4)
        
        if custom_instruction and self.is_flan:
            input_text = f"{custom_instruction}: {text}"
        else:
            input_text = f"summarize: {text}"
        
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                length_penalty=1.5,
                early_stopping=True,
                no_repeat_ngram_size=3,
                repetition_penalty=1.2,
                temperature=1.0
            )
        
        summary = self.tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )
        return summary

    def _summarize_long_text(self, text, summary_config, quality, custom_instruction):
        """Handle long texts with intelligent chunking"""
        chunk_size = 400
        words = text.split()
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        print(f"  📄 Processing {len(chunks)} chunk(s)...")
        
        chunk_summaries = []
        for idx, chunk in enumerate(chunks):
            chunk_words = len(chunk.split())
            if chunk_words < 25:
                continue
            
            chunk_config = self.calculate_adaptive_summary_length(chunk_words, summary_config['strategy'])
            try:
                chunk_summary = self.generate_t5_summary(
                    chunk,
                    max_length=chunk_config['max_length'],
                    min_length=chunk_config['min_length'],
                    quality=quality,
                    custom_instruction=custom_instruction
                )
                chunk_summaries.append(chunk_summary)
            except Exception as e:
                print(f"✗ Chunk error: {e}")
                continue
        
        if not chunk_summaries:
            return text[:500]
        
        combined = ' '.join(chunk_summaries)
        combined_words = len(combined.split())
        
        if len(chunks) > 1 and combined_words > summary_config['max_words']:
            try:
                final = self.generate_t5_summary(
                    combined,
                    max_length=summary_config['max_length'],
                    min_length=summary_config['min_length'],
                    quality=quality,
                    custom_instruction=custom_instruction
                )
                return final
            except:
                pass
        
        return combined

    def extract_structured_info(self, text):
        """Extract structured information from text/summary"""
        info = {
            'requirements': [],
            'decisions': [],
            'action_items': [],
            'timeline': [],
            'budget': [],
            'risks': [],
            'technical': [],
            'deliverables': [],
            'stakeholders': []
        }
        
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence: continue
            lower = sentence.lower()
            
            if any(w in lower for w in ['require', 'need', 'must', 'should', 'shall', 'expect']):
                info['requirements'].append(sentence)
            if any(w in lower for w in ['decide', 'agreed', 'approved', 'confirmed', 'finalized']):
                info['decisions'].append(sentence)
            if any(w in lower for w in ['will', 'task', 'action', 'assign', 'responsible', 'owner']):
                info['action_items'].append(sentence)
            if any(w in lower for w in ['deadline', 'timeline', 'date', 'week', 'month', 'schedule', 'due']):
                info['timeline'].append(sentence)
            if any(w in lower for w in ['cost', 'budget', 'price', 'payment', 'fund', 'expense', '$', 'rs', 'rupee', 'inr']):
                info['budget'].append(sentence)
            if any(w in lower for w in ['risk', 'concern', 'issue', 'challenge', 'problem', 'blocker']):
                info['risks'].append(sentence)
            if any(w in lower for w in ['technical', 'technology', 'system', 'platform', 'api', 'database', 'infrastructure']):
                info['technical'].append(sentence)
            if any(w in lower for w in ['deliver', 'output', 'product', 'feature', 'component', 'milestone']):
                info['deliverables'].append(sentence)
            if any(w in lower for w in ['stakeholder', 'team', 'department', 'client', 'customer', 'vendor']):
                info['stakeholders'].append(sentence)
        
        return info

    def generate_brd(self, summary_text, structured_info, metadata):
        """Generate Business Requirements Document"""
        doc = f"""
{'='*80}
BUSINESS REQUIREMENTS DOCUMENT (BRD)
{'='*80}

Document Information:
--------------------
Project Name:     {metadata.get('project_name', 'Auto-Generated Project')}
Document Date:    {metadata.get('date', datetime.now().strftime('%Y-%m-%d'))}
Version:          {metadata.get('version', '1.0')}
Prepared By:      {metadata.get('author', 'Smart T5 AI System')}
Status:           {metadata.get('status', 'Draft')}
Department:       {metadata.get('department', 'TBD')}
Sponsor:          {metadata.get('sponsor', 'TBD')}


1. EXECUTIVE SUMMARY
{'='*80}

{summary_text}


2. BUSINESS OBJECTIVES
{'='*80}

Based on the provided information, the key business objectives are:

"""
        if structured_info['requirements']:
            for idx, req in enumerate(structured_info['requirements'][:5], 1):
                doc += f"OBJ-{idx}: {req}\n"
        else:
            doc += "Business objectives to be refined based on stakeholder review.\n"
        
        doc += f"""

3. BUSINESS REQUIREMENTS
{'='*80}

"""
        if structured_info['requirements']:
            for idx, req in enumerate(structured_info['requirements'], 1):
                doc += f"BR-{idx:03d}: {req}\n"
                doc += f"         Priority: {metadata.get('priority', 'Medium')}\n"
                doc += f"         Source: AI Extraction\n\n"
        else:
            doc += "Business requirements extracted from executive summary above.\n"
            
        # ... (Additional sections like Functional Requirements, Stakeholders etc could be added here similar to notebook)
        # For brevity preserving the key ones and extracting logical rest from memory/previous impl
        
        doc += f"""

4. STAKEHOLDERS
{'='*80}

"""
        if structured_info['stakeholders']:
            for s in structured_info['stakeholders']:
                doc += f"• {s}\n"
        else:
            doc += "Stakeholders to be identified.\n"

        doc += f"""

5. TIMELINE
{'='*80}

"""
        if structured_info['timeline']:
            for t in structured_info['timeline']:
                doc += f"• {t}\n"
        else:
            doc += "Timeline to be determined.\n"

        doc += f"""

{'='*80}
Document Generated by Smart T5 AI System
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
"""
        return doc

    def generate_purchase_order(self, summary_text, structured_info, metadata):
        """Generate Purchase Order"""
        doc = f"""
{'='*80}
PURCHASE ORDER
{'='*80}

PO Number:        {metadata.get('po_number', 'PO-' + datetime.now().strftime('%Y%m%d-%H%M'))}
Date:             {metadata.get('date', datetime.now().strftime('%Y-%m-%d'))}
Status:           {metadata.get('status', 'Draft')}

VENDOR INFORMATION:
{'='*80}
Vendor Name:      {metadata.get('vendor_name', 'TBD')}
Vendor Email:     {metadata.get('vendor_email', 'TBD')}


BUYER INFORMATION:
{'='*80}
Company Name:     {metadata.get('company_name', 'Your Company Ltd.')}

PURCHASE ORDER SUMMARY:
{'='*80}

{summary_text}


DETAILED LINE ITEMS:
{'='*80}

"""
        items = structured_info['deliverables'] if structured_info['deliverables'] else structured_info['requirements']
        
        doc += f"{'Item':<5} {'Description':<45} {'Qty':<8} {'Unit':<10} {'Price':<12} {'Total':<12}\n"
        doc += "-" * 100 + "\n"
        
        if items:
            for idx, item in enumerate(items[:15], 1):
                clean_item = item.replace('\n', ' ')[:42]
                doc += f"{idx:<5} {clean_item:<45} {'TBD':<8} {'Each':<10} {'TBD':<12} {'TBD':<12}\n"
        else:
            doc += f"{'1':<5} {'Items/Services as per discussion':<45} {'TBD':<8} {'Each':<10} {'TBD':<12} {'TBD':<12}\n"
            
        doc += f"""

COST BREAKDOWN:
{'='*80}

"""
        if structured_info['budget']:
            for b in structured_info['budget']:
                doc += f"• {b}\n"
        
        doc += f"""
TOTAL AMOUNT:                                                {metadata.get('total_amount', 'TBD')}
                                                             ===========
"""
        return doc

    def process_audio_smart(self, audio_path, strategy='balanced', quality='medium', custom_instruction=None, save_output=False, output_filename=None, diarize=False):
        """
        Complete smart pipeline with T5 adaptive summarization AND Optional Diarization
        """
        print("="*70)
        print("🎯 SMART T5 AUDIO SUMMARIZER")
        print("="*70 + "\\n")
        
        # Step 1: Transcribe
        transcription_result = self.transcribe_audio(audio_path)
        full_text = transcription_result['text']
        word_count = transcription_result['word_count']
        
        # Step 1.5: Diarization (Optional)
        final_transcript_text = full_text # Default to plain text
        speakers_detected = 0
        
        if diarize:
            print("🔍 Diarization requested...")
            speaker_segments = self.diarize_audio(
                audio_path, 
                min_speakers=config.MIN_SPEAKERS, 
                max_speakers=config.MAX_SPEAKERS
            )
            
            if speaker_segments:
                merged = self.merge_transcription_with_diarization(transcription_result['segments'], speaker_segments)
                final_transcript_text = self.format_transcript_with_speakers(merged)
                speakers_detected = len(set(s['speaker'] for s in merged))
                # Use the speaker-annotated transcript for summarization? 
                # Yes, FLAN-T5 handles it well and can extract speaker-specific info.
                print("✅ Using speaker-annotated transcript for summarization.")
                
                # Check if we should switch to a better summarization instruction
                if not custom_instruction:
                     custom_instruction = "Summarize the meeting, clearly identifying main points raised by each speaker"
            else:
                print("⚠️ Diarization returned no segments, falling back to plain transcription.")

        # Step 2: Calculate smart summary length
        print(f"🧠 Calculating adaptive summary length...")
        summary_config = self.calculate_adaptive_summary_length(word_count, strategy)
        
        # Step 3: Handle very short text
        if word_count < 25:
            print("⚠️ Text very short (<25 words) - returning full transcription")
            summary = final_transcript_text
            summary_words = word_count
        else:
            print(f"📊 Generating T5 summary (process_audio_smart)...")
            
            # Use final_transcript_text which might contain speaker labels
            text_to_summarize = final_transcript_text
            
            if word_count > 400:
                summary = self._summarize_long_text(
                    text_to_summarize,
                    summary_config,
                    quality,
                    custom_instruction
                )
            else:
                summary = self.generate_t5_summary(
                    text_to_summarize,
                    max_length=summary_config['max_length'],
                    min_length=summary_config['min_length'],
                    quality=quality,
                    custom_instruction=custom_instruction
                )
            summary_words = len(summary.split())
        
        results = {
            'audio_file': os.path.basename(audio_path),
            'language': transcription_result['language_name'],
            'transcription': final_transcript_text,
            'summary': summary,
            'input_words': word_count,
            'summary_words': summary_words,
            'compression_ratio': (1 - summary_words/word_count) * 100 if word_count > 0 else 0,
            'strategy': strategy,
            'quality': quality,
            'config': summary_config
        }
        
        if save_output and output_filename:
            # Implement file saving logic if needed
            pass
            
        return results

# Global instance
_document_generator = None

def get_generator():
    global _document_generator
    if _document_generator is None:
        # Load both models for full functionality
        _document_generator = SmartT5LargeDocumentGenerator()
    return _document_generator

def generate_document(text, document_type, metadata=None):
    """
    Main function to generate documents using the smart generator from TEXT input.
    Use this if you already have text (e.g. from frontend notes).
    """
    if metadata is None:
        metadata = {}
    
    generator = get_generator()
    
    # Generate summary first to get structured info
    word_count = len(text.split())
    if word_count > 50:
        print(f"Generating abstractive summary for {word_count} words...")
        summary = generator.generate_t5_summary(
            text,
            max_length=512,
            min_length=min(100, word_count),
            quality='medium'
        )
    else:
        summary = text
        
    print(f"Extracting structured info from summary...")
    structured_info = generator.extract_structured_info(summary)
    
    # Also extract from original text (hybrid)
    raw_info = generator.extract_structured_info(text)
    for key in structured_info:
        structured_info[key].extend(raw_info[key])
        structured_info[key] = list(set(structured_info[key]))
    
    if document_type == 'brd':
        return generator.generate_brd(summary, structured_info, metadata)
    elif document_type == 'po':
        return generator.generate_purchase_order(summary, structured_info, metadata)
    else:
        raise ValueError(f"Unknown document type: {document_type}")
