import os
from pathlib import Path
from openai import OpenAI
import time
import shutil

def get_valid_input_file():
    """Prompt user for input file and validate it exists."""
    while True:
        file_path = input("Please enter the path to your text file: ").strip()
        if os.path.isfile(file_path):
            return file_path
        print(f"Error: File '{file_path}' does not exist. Please try again.")

def split_text(text, max_length=4000):
    """Split text into chunks that TTS can handle, trying to break at sentences."""
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

def text_to_speech(client, text_chunk, output_dir, chunk_num):
    """Convert text chunk to speech using OpenAI's API."""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text_chunk
        )
        
        # Save temporary chunk
        temp_path = output_dir / f"chunk_{chunk_num:04d}.mp3"
        response.stream_to_file(temp_path)
        
        return temp_path
    except Exception as e:
        print(f"Error processing chunk {chunk_num}: {e}")
        return None

def concatenate_audio_files(audio_files, output_file):
    """Concatenate MP3 files using direct file writing."""
    with open(output_file, 'wb') as outfile:
        # Write the first file completely
        with open(audio_files[0], 'rb') as firstfile:
            shutil.copyfileobj(firstfile, outfile)
        
        # Append the rest of the files
        for file_path in audio_files[1:]:
            with open(file_path, 'rb') as infile:
                shutil.copyfileobj(infile, outfile)

def process_file(input_file):
    """Process entire text file to speech."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
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
        print(f"Text split into {total_chunks} chunks")
        
        # Process each chunk
        audio_files = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{total_chunks}")
            
            temp_path = text_to_speech(client, chunk, output_dir, i)
            if temp_path:
                audio_files.append(temp_path)
            
            # Add a small delay to avoid rate limits
            time.sleep(1)
        
        if audio_files:
            # Combine all audio files
            print("\nCombining audio files...")
            concatenate_audio_files([str(f) for f in audio_files], output_file)
            print(f"Audio book saved to: {output_file}")
        
        # Clean up temporary files
        for file in audio_files:
            file.unlink()
        output_dir.rmdir()
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Make sure OPENAI_API_KEY is set in environment variables
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    # Get input file from user
    input_file = get_valid_input_file()
    
    print(f"Input file: {input_file}")
    print(f"Output will be saved as: {Path(input_file).stem}_audiobook.mp3")
    
    # Confirm with user
    if input("Proceed? (y/n): ").lower().strip() != 'y':
        print("Operation cancelled.")
        exit()
    
    process_file(input_file)