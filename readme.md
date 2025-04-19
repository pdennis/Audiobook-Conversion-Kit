# Audiobook Conversion Kit

When I scan a paper book and OCR the results, I generally get a readable, but slightly messy file. This is a toolkit for turning those files into listenable audiobooks.

There are two tools: 

1. A text cleanup tool using GPT-4o-mini, for making sure OCR artefacts and other non-audiobook friendly text is cleaned up. 
2. An audiobook conversion tool using OpenAI's TTS-1 model, to convert the text file to MP3

## Text Cleanup Tool

This script helps clean up text files by processing them through GPT-4o-mini. It handles common artifacts, formatting issues, and breaks the text into manageable chunks while preserving natural language boundaries.

### Features
- Splits text into chunks at natural boundaries (newlines and sentences)
- Processes each chunk through GPT-4o-mini for cleanup
- Preserves document structure
- Includes progress tracking and temporary save files
- Automatically generates output filename
- Validates input files and user confirmation

## Audiobook Conversion Tool

This script converts text files into audiobooks using the MLX-Audio text-to-speech engine, optimized for Apple Silicon.

### Features
- Converts entire text files to speech
- Uses MLX-Audio TTS engine (fast inference on Apple Silicon)
- Multiple voice options (af_heart, af_nova, af_bella, bf_emma)
- Adjustable speech speed (0.5x to 2.0x)
- Splits text into processable chunks at sentence boundaries
- Combines all audio chunks into a single WAV file
- Includes progress tracking
- Cleans up temporary files automatically

## Prerequisites
- Python 3.6 or higher
- Apple Silicon Mac (for optimal MLX-Audio performance)
- OpenAI API key (only for text cleanup tool)

## Installation

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your OpenAI API key as an environment variable:
   ```bash
   # For Unix/Linux/macOS
   export OPENAI_API_KEY='your-key-here'
   
   # For Windows (PowerShell)
   $env:OPENAI_API_KEY='your-key-here'
   ```

## Usage

### Text Cleanup
1. Run the script:
   ```bash
   python book_cleanup.py
   ```
2. When prompted, enter the path to your text file
3. Review the output path (will be original_filename_cleaned.txt)
4. Confirm to proceed

### Audiobook Conversion
1. Run the script:
   ```bash
   python audiobook.py
   ```
2. When prompted, enter the path to your text file
3. Choose a voice from the available options
4. Set the speech speed (between 0.5 and 2.0)
5. Review the output path (will be original_filename_audiobook.wav)
6. Confirm to proceed

## Output Files

### Text Cleanup
- The cleaned text will be saved to a new file with '_cleaned' appended to the original filename
- Example: `book.txt` → `book_cleaned.txt`
- A temporary `.partial` file is created during processing and automatically removed upon completion

### Audiobook
- The audio will be saved to a new file with '_audiobook.wav' appended to the original filename
- Example: `book.txt` → `book_audiobook.wav`
- Temporary audio chunks are created during processing and automatically removed upon completion

## Error Handling
- Validates input file existence
- Maintains partial progress in case of interruption
- Preserves original text/audio if processing fails for any chunk
- Cleans up temporary files even if processing is interrupted

## Notes
- Text cleanup default chunk size is 2000 characters
- Audio conversion chunk size is 4000 characters (OpenAI TTS limit)
- Both scripts require an active internet connection
- Processing time and cost will depend on:
  - The size of your input file
  - Current OpenAI API rates
  - Network speed and stability

