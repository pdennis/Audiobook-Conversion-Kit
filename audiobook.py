import os
from pathlib import Path
import time
import soundfile as sf
from loguru import logger
from mlx_audio.tts.generate import generate_audio

def get_valid_input_file():
    """Prompt user for input file and validate it exists."""
    while True:
        file_path = input("Please enter the path to your text file: ").strip()
        if os.path.isfile(file_path):
            return file_path
        print(f"Error: File '{file_path}' does not exist. Please try again.")

def choose_voice():
    """Prompt user to choose a voice."""
    voices = [
        'af_heart', 'af_nova', 'af_bella', 'bf_emma'
    ]
    print("\nAvailable voices:")
    for i, voice in enumerate(voices, 1):
        print(f"{i}. {voice}")

    while True:
        choice = input("\nChoose a voice by number (1-4) or name: ").strip().lower()
        if choice.isdigit() and 1 <= int(choice) <= len(voices):
            return voices[int(choice) - 1]
        elif choice in voices:
            return choice
        else:
            print("Invalid choice. Please enter a number from 1-4 or a valid voice name.")

def choose_speech_speed():
    """Let user choose speech speed."""
    while True:
        try:
            speed = float(input("\nEnter speech speed (0.5-2.0): ").strip())
            if 0.5 <= speed <= 2.0:
                return speed
            print("Speed must be between 0.5 and 2.0")
        except ValueError:
            print("Please enter a valid number")

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

def text_to_speech(text_chunk, output_dir, chunk_num, voice, speed):
    """Convert text chunk to speech using MLX-Audio."""
    try:
        temp_path = output_dir / f"chunk_{chunk_num:04d}.wav"
        
        # Generate audio using MLX-Audio
        generate_audio(
            text=text_chunk,
            voice=voice,
            speed=speed,
            lang_code=voice[0],  # 'a' for US English, 'b' for UK English
            file_prefix=str(temp_path.with_suffix('')),
            audio_format="wav",
            sample_rate=24000,
            join_audio=True,
            verbose=False  # Disable print messages to avoid cluttering output
        )
        
        logger.info(f"Saved chunk {chunk_num}")
        return temp_path
    except Exception as e:
        logger.error(f"Error processing chunk {chunk_num}: {e}")
        return None

def concatenate_audio_files(audio_files, output_file):
    """Concatenate audio files and save as MP3 if output is MP3."""
    import numpy as np
    from pydub import AudioSegment
    
    # Read the first file to get parameters
    data, sample_rate = sf.read(audio_files[0])
    total_data = [data]
    
    # Read and append the rest
    for file_path in audio_files[1:]:
        data, _ = sf.read(file_path)
        total_data.append(data)
    
    # Combine all audio data
    combined = np.concatenate(total_data)
    
    # Check if output is MP3
    if output_file.suffix.lower() == '.mp3':
        # First save as temporary WAV
        temp_wav = output_file.with_suffix('.wav')
        sf.write(temp_wav, combined, sample_rate)
        
        # Convert to MP3 using pydub
        audio = AudioSegment.from_wav(temp_wav)
        audio.export(output_file, format="mp3")
        
        # Remove temporary WAV file
        os.remove(temp_wav)
    else:
        # Write the combined file as WAV
        sf.write(output_file, combined, sample_rate)

def process_file(input_file, voice, speed):
    """Process entire text file to speech."""
    # Create output directory for temporary files
    input_path = Path(input_file)
    output_dir = input_path.parent / f"{input_path.stem}_tts_temp"
    output_dir.mkdir(exist_ok=True)
    
    # Final output file path
    output_file = input_path.parent / f"{input_path.stem}_audiobook.mp3"
    
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
            
            temp_path = text_to_speech(chunk, output_dir, i, voice, speed)
            if temp_path:
                audio_files.append(temp_path)
            
            # Small delay between chunks
            time.sleep(0.1)
        
        if audio_files:
            # Combine all audio files
            logger.info("\nCombining audio files...")
            concatenate_audio_files([str(f) for f in audio_files], output_file)
            logger.info(f"Audio book saved to: {output_file}")
            
            # Update podcast feed
            try:
                from podcast_feed import update_feed_after_audiobook
                feed_path = update_feed_after_audiobook(output_file)
                logger.info(f"Updated podcast feed: {feed_path}")
            except Exception as feed_error:
                logger.error(f"Failed to update podcast feed: {feed_error}")
        
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
    logger.info(f"Output will be saved as: {Path(input_file).stem}_audiobook.mp3")
    
    # Choose voice
    voice = choose_voice()
    logger.info(f"Selected voice: {voice}")
    
    # Choose speech speed
    speed = choose_speech_speed()
    logger.info(f"Selected speed: {speed}")
    
    # Confirm with user
    if input("Proceed? (y/n): ").lower().strip() != 'y':
        logger.info("Operation cancelled.")
        exit()
    
    process_file(input_file, voice, speed)