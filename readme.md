# Book Text Cleanup Tool

This Python script helps clean up text files (such as those extracted from PDFs or ebooks) by processing them through GPT-4o-mini. It handles common artifacts, formatting issues, and breaks the text into manageable chunks while preserving natural language boundaries.

## Features

- Splits text into chunks at natural boundaries (newlines and sentences)
- Processes each chunk through GPT-4o-mini for cleanup
- Preserves document structure
- Includes progress tracking and temporary save files
- Automatically generates output filename
- Validates input files and user confirmation

## Prerequisites

- Python 3.6 or higher
- OpenAI API key

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

1. Run the script:
   ```bash
   python book_cleanup.py
   ```

2. When prompted, enter the path to your text file
3. Review the output path (will be original_filename_cleaned.txt)
4. Confirm to proceed

The script will process your file and show progress as it works through each chunk.

## Output

- The cleaned text will be saved to a new file with '_cleaned' appended to the original filename
- Example: `book.txt` → `book_cleaned.txt`
- A temporary `.partial` file is created during processing and automatically removed upon completion

## Error Handling

- Validates input file existence
- Maintains partial progress in case of interruption
- Preserves original text if GPT-4o-mini processing fails for any chunk

## Notes

- Default chunk size is 2000 characters but splits occur at natural boundaries
- The script requires an active internet connection for GPT-4o-mini processing
- Processing time and cost will depend on the size of your input file and current OpenAI API rates


