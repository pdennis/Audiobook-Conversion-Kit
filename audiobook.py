import os
from pathlib import Path
from kokoro import KPipeline, KModel
import time
import soundfile as sf
from loguru import logger
import torch

def get_valid_input_file():
    """Prompt user for input file and validate it exists."""
    while True:
        file_path = input("Please enter the path to your text file: ").strip()
        if os.path.isfile(file_path):
            return file_path
        print(f"Error: File '{file_path}' does not exist. Please try again.")

def choose_device():
    """Let user choose between GPU and CPU if GPU is available."""
    cuda_available = torch.cuda.is_available()
    if not cuda_available:
        logger.info("GPU not available, using CPU")
        return False
        
    while True:
        choice = input("\nUse GPU for faster processing? (y/n): ").strip().lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        print("Please enter 'y' or 'n'")

def process_file(input_file, voice, use_gpu=False):
    """Process entire text file to speech."""
    # Initialize Kokoro pipeline and model
    if use_gpu and not torch.cuda.is_available():
        logger.warning("GPU requested but not available, falling back to CPU")
        use_gpu = False
        
    model = KModel().to('cuda' if use_gpu else 'cpu').eval()
    pipeline = KPipeline(lang_code=voice[0])

def choose_voice():
    """Prompt user to choose a voice."""
    voices = [
        'af_heart', 'af_bella', 'af_nicole', 'af_aoede', 'af_kore',
        'af_sarah', 'af_nova', 'af_sky', 'af_alloy', 'af_jessica',
        'af_river', 'am_michael', 'am_fenrir', 'am_puck', 'am_echo',
        'am_eric', 'am_liam', 'am_onyx', 'am_santa', 'am_adam',
        'bf_emma', 'bf_isabella', 'bf_alice', 'bf_lily',
        'bm_george', 'bm_fable', 'bm_lewis', 'bm_daniel'
    ]
    print("\nAvailable voices:")
    for i, voice in enumerate(voices, 1):
        print(f"{i}. {voice}")

    while True:
        choice = input("\nChoose a voice by number (1-28) or name: ").strip().lower()
        if choice.isdigit() and 1 <= int(choice) <= len(voices):
            return voices[int(choice) - 1]
        elif choice in voices:
            return choice
        else:
            print("Invalid choice. Please enter a number from 1-28 or a valid voice name.")

def split_text(text, max_length=500):
    """Split text into chunks, trying to break at sentences."""
    chunks = []
    current_chunk = []
    current_length = 0
    
    # Split into sentences first (basic implementation)
    sentences = text.replace('\n', ' ').split('. ')
    
    for sentence in sentences:
        # Add period back if it was removed (except for last sentence)
        sentence = sentence + '. ' if sentence != sentences[-1] else sentence
        
        if current_length + len(sentence) > max_length:
            if current_chunk:
                chunks.append(''.join(current_chunk))
                current_chunk = []
                current_length = 0
        
        current_chunk.append(sentence)
        current_length += len(sentence)
    
    if current_chunk:
        chunks.append(''.join(current_chunk))
    
    return chunks

def initialize_model(use_gpu=False):
    """Initialize the Kokoro model with proper device selection."""
    model = KModel()
    if use_gpu and torch.cuda.is_available():
        model = model.to('cuda')
        logger.info("Using GPU for synthesis")
    else:
        model = model.to('cpu')
        logger.info("Using CPU for synthesis")
    return model.eval()

def text_to_speech(pipeline, model, text_chunk, output_dir, chunk_num, voice):
    """Convert text chunk to speech using Kokoro."""
    try:
        temp_path = output_dir / f"chunk_{chunk_num:04d}.wav"
        pack = pipeline.load_voice(voice)
        
        for _, ps, _ in pipeline(text_chunk, voice):
            if ps:  # Check if we got phoneme sequence
                ref_s = pack[len(ps)-1]
                audio = model(ps, ref_s, speed=1.0)
                if audio is not None:
                    # Save the audio chunk
                    sf.write(temp_path, audio.cpu().numpy(), 24000)  # Kokoro uses 24kHz
                    logger.info(f"Saved chunk {chunk_num}")
                    return temp_path
            
        return None
    except Exception as e:
        logger.error(f"Error processing chunk {chunk_num}: {e}")
        return None

def concatenate_audio_files(audio_files, output_file):
    """Concatenate WAV files."""
    import numpy as np
    
    # Read the first file to get parameters
    data, sample_rate = sf.read(audio_files[0])
    total_data = [data]
    
    # Read and append the rest
    for file_path in audio_files[1:]:
        data, _ = sf.read(file_path)
        total_data.append(data)
    
    # Combine all audio data
    combined = np.concatenate(total_data)
    
    # Write the combined file
    sf.write(output_file, combined, sample_rate)

def process_file(input_file, voice):
    """Process entire text file to speech."""
    # Initialize Kokoro pipeline and model
    use_gpu = torch.cuda.is_available()
    model = initialize_model(use_gpu)
    pipeline = KPipeline(lang_code=voice[0])  # 'a' for US English, 'b' for UK English
    
    # Create output directory for temporary files
    input_path = Path(input_file)
    output_dir = input_path.parent / f"{input_path.stem}_tts_temp"
    output_dir.mkdir(exist_ok=True)
    
    # Final output file path
    output_file = input_path.parent / f"{input_path.stem}_audiobook.wav"
    
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Split into chunks
        chunks = split_text(text)
        total_chunks = len(chunks)
        logger.info(f"Text split into {total_chunks} chunks")
        
        # Process each chunk
        audio_files = []
        
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{total_chunks}")
            
            temp_path = text_to_speech(pipeline, model, chunk, output_dir, i, voice)
            if temp_path:
                audio_files.append(temp_path)
            
            # Small delay between chunks
            time.sleep(0.1)
        
        if audio_files:
            # Combine all audio files
            logger.info("\nCombining audio files...")
            concatenate_audio_files([str(f) for f in audio_files], output_file)
            logger.info(f"Audio book saved to: {output_file}")
        
        # Clean up temporary files
        for file in audio_files:
            file.unlink()
        output_dir.rmdir()
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Get input file from user
    input_file = get_valid_input_file()
    
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output will be saved as: {Path(input_file).stem}_audiobook.wav")
    
    # Choose voice
    voice = choose_voice()
    logger.info(f"Selected voice: {voice}")
    
    # Choose device
    use_gpu = choose_device()
    device_type = "GPU" if use_gpu else "CPU"
    logger.info(f"Using {device_type} for processing")
    
    # Confirm with user
    if input("Proceed? (y/n): ").lower().strip() != 'y':
        logger.info("Operation cancelled.")
        exit()
    
    process_file(input_file, voice, use_gpu)