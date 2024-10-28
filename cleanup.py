import os
from openai import OpenAI
from pathlib import Path

def clean_text_with_gpt4(text_chunk):
    """Send text chunk to GPT-4 for cleanup."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = """Clean up this text that was extracted from a PDF. Remove OCR artifacts, fix formatting issues, and make it readable. Remove page numbers or repeated chapter identifiers that exist on every page. Otherwise, preserve the origional content. Only output the final text, no additional commentary or description of the task. Text:   {text} """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that cleans up OCR text into scripts for audiobooks."},
                {"role": "user", "content": prompt.format(text=text_chunk)}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing chunk: {e}")
        return text_chunk

def split_into_chunks(text, max_chunk_size=2000):
    """Split text into chunks at natural boundaries."""
    chunks = []
    current_chunk = []
    current_size = 0
    
    # Split into lines first
    lines = text.split('\n')
    
    for line in lines:
        # If adding this line would exceed max_chunk_size
        if current_size + len(line) + 1 > max_chunk_size and current_chunk:
            # Join the current chunk and add to chunks list
            chunks.append('\n'.join(current_chunk))
            # Start new chunk
            current_chunk = []
            current_size = 0
        
        # If a single line is longer than max_chunk_size, split it at sentence boundaries
        if len(line) > max_chunk_size:
            # Common sentence endings
            separators = ['. ', '! ', '? ', '; ']
            current_sentence = []
            words = line.split(' ')
            
            for word in words:
                current_sentence.append(word)
                sentence_text = ' '.join(current_sentence)
                
                # Check if any sentence endings are in the last word
                ends_with_separator = any(word.endswith(sep.strip()) for sep in separators)
                
                if (len(sentence_text) > max_chunk_size or ends_with_separator) and current_sentence:
                    if current_chunk:
                        chunks.append('\n'.join(current_chunk))
                    chunks.append(sentence_text)
                    current_chunk = []
                    current_sentence = []
                    current_size = 0
        else:
            current_chunk.append(line)
            current_size += len(line) + 1  # +1 for newline
    
    # Add the last chunk if there is one
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def process_text_file(input_file, output_file, chunk_size=2000):
    """Process text file in chunks and clean with GPT-4."""
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split into chunks at natural boundaries
    chunks = split_into_chunks(text, chunk_size)
    
    # Process each chunk
    cleaned_chunks = []
    total_chunks = len(chunks)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Processing chunk {i}/{total_chunks}")
        cleaned_chunk = clean_text_with_gpt4(chunk)
        cleaned_chunks.append(cleaned_chunk)
        
        # Optional: Write progress to temporary file
        with open(f"{output_file}.partial", 'w', encoding='utf-8') as f:
            f.write('\n'.join(cleaned_chunks))
    
    # Write final output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_chunks))
    
    # Clean up temporary file
    if os.path.exists(f"{output_file}.partial"):
        os.remove(f"{output_file}.partial")

def get_valid_input_file():
    """Prompt user for input file and validate it exists."""
    while True:
        file_path = input("Please enter the path to your text file: ").strip()
        if os.path.isfile(file_path):
            return file_path
        print(f"Error: File '{file_path}' does not exist. Please try again.")

if __name__ == "__main__":
    # Make sure OPENAI_API_KEY is set in environment variables
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    # Get input file from user
    input_file = get_valid_input_file()
    
    # Create output filename by appending '_cleaned' before the extension
    input_path = Path(input_file)
    output_file = str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}")
    
    print(f"Input file: {input_file}")
    print(f"Output will be saved to: {output_file}")
    
    # Confirm with user
    if input("Proceed? (y/n): ").lower().strip() != 'y':
        print("Operation cancelled.")
        exit()
    
    process_text_file(input_file, output_file)
    print(f"Processing complete. Cleaned text saved to {output_file}")