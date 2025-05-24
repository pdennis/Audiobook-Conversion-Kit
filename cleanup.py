import os
from pathlib import Path
import ollama

def clean_text_with_ollama(text_chunk, model_name):
    """Send text chunk to Ollama model for cleanup."""
    prompt = """Clean up this text that was extracted from a PDF. Remove OCR artifacts, fix formatting issues, and make it readable. Remove page numbers or repeated chapter identifiers that exist on every page. Otherwise, preserve the original content. Only output the final text, no additional commentary or description of the task. Text:   {text} """
    
    # Remove 'ollama run' prefix if present
    if model_name.startswith('ollama run '):
        model_name = model_name.replace('ollama run ', '')
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that cleans up OCR text into scripts for audiobooks."},
                {"role": "user", "content": prompt.format(text=text_chunk)}
            ]
        )
        return response.message.content
    except Exception as e:
        print(f"Error processing chunk: {e}")
        return text_chunk

def split_into_chunks(text, max_chunk_size=3000, min_chunk_size=1500):
    """Split text into chunks at natural boundaries while maintaining context."""
    chunks = []
    current_chunk = []
    current_size = 0
    
    # Split into paragraphs first (double newlines indicate paragraphs)
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # If this paragraph would exceed max_chunk_size
        if current_size + len(paragraph) + 2 > max_chunk_size:
            # Only create a new chunk if we have enough content
            if current_size >= min_chunk_size:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # If a single paragraph is longer than max_chunk_size
            if len(paragraph) > max_chunk_size:
                # Split at sentence boundaries
                sentences = []
                current_sentence = []
                words = paragraph.split(' ')
                
                for word in words:
                    current_sentence.append(word)
                    sentence_text = ' '.join(current_sentence)
                    
                    # Check for sentence endings
                    ends_with_separator = any(
                        word.endswith(sep) 
                        for sep in ['.', '!', '?', ';']
                    )
                    
                    if ends_with_separator and len(sentence_text) > min_chunk_size:
                        sentences.append(sentence_text)
                        current_sentence = []
                
                # Add any remaining sentence
                if current_sentence:
                    sentences.append(' '.join(current_sentence))
                
                # Combine sentences into chunks of appropriate size
                temp_chunk = []
                temp_size = 0
                
                for sentence in sentences:
                    if temp_size + len(sentence) + 1 <= max_chunk_size:
                        temp_chunk.append(sentence)
                        temp_size += len(sentence) + 1
                    else:
                        if temp_chunk:
                            chunks.append(' '.join(temp_chunk))
                        temp_chunk = [sentence]
                        temp_size = len(sentence)
                
                if temp_chunk:
                    current_chunk.append(' '.join(temp_chunk))
                    current_size = temp_size
            else:
                current_chunk.append(paragraph)
                current_size += len(paragraph) + 2
        else:
            current_chunk.append(paragraph)
            current_size += len(paragraph) + 2
    
    # Add the final chunk if there is one
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def get_available_models():
    """Get list of available Ollama models."""
    try:
        models = ollama.list()
        return [model['name'] for model in models['models']]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def process_text_file(input_file, output_file, model_name, chunk_size=2000):
    """Process text file in chunks and clean with Ollama model."""
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
        cleaned_chunk = clean_text_with_ollama(chunk, model_name)
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

def select_model():
    """Let user select from available models or specify a different one."""
    available_models = get_available_models()
    
    if available_models:
        print("\nAvailable models:")
        for i, model in enumerate(available_models, 1):
            print(f"{i}. {model}")
        print(f"{len(available_models) + 1}. Specify a different model")
        
        while True:
            try:
                choice = int(input("\nSelect a model (enter number): "))
                if 1 <= choice <= len(available_models):
                    return available_models[choice - 1]
                elif choice == len(available_models) + 1:
                    return input("Enter model name: ").strip()
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
    else:
        return input("Enter model name (e.g., 'llama2'): ").strip()

if __name__ == "__main__":
    print("Text Cleanup Script using Ollama")
    print("--------------------------------")
    
    # Get input file from user
    input_file = get_valid_input_file()
    
    # Create output filename by appending '_cleaned' before the extension
    input_path = Path(input_file)
    output_file = str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}")
    
    # Select model
    model_name = select_model()
    
    print(f"\nInput file: {input_file}")
    print(f"Selected model: {model_name}")
    print(f"Output will be saved to: {output_file}")
    
    # Confirm with user
    if input("\nProceed? (y/n): ").lower().strip() != 'y':
        print("Operation cancelled.")
        exit()
    
    process_text_file(input_file, output_file, model_name)
    print(f"\nProcessing complete. Cleaned text saved to {output_file}")