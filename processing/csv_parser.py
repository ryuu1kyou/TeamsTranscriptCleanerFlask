"""
CSV parser for Teams transcript files.
"""
import csv
import io
import re
from typing import List, Dict, Any


def parse_csv_text(csv_content: str) -> Dict[str, Any]:
    """
    Parse Teams transcript CSV content and extract text.
    
    Args:
        csv_content: Raw CSV content as string
        
    Returns:
        Dictionary with parsed content and metadata
    """
    try:
        # Create a StringIO object from the CSV content
        csv_file = io.StringIO(csv_content)
        csv_reader = csv.reader(csv_file)
        
        # Skip header if present
        headers = next(csv_reader, None)
        if not headers:
            return {
                'success': False,
                'error': 'Empty CSV file',
                'text': '',
                'metadata': {}
            }
        
        # Extract text content
        transcript_lines = []
        speaker_count = 0
        timestamp_pattern = re.compile(r'\d{1,2}:\d{2}:\d{2}')
        
        for row in csv_reader:
            if len(row) >= 2:  # Assuming timestamp and speaker/text columns
                # Simple text extraction - can be enhanced based on actual CSV format
                text_content = ' '.join(row[1:]).strip()
                if text_content:
                    # Remove timestamps if present
                    cleaned_text = timestamp_pattern.sub('', text_content).strip()
                    if cleaned_text:
                        transcript_lines.append(cleaned_text)
                        
        # Join all lines
        full_text = '\n'.join(transcript_lines)
        
        # Calculate basic statistics
        word_count = len(full_text.split())
        character_count = len(full_text)
        
        return {
            'success': True,
            'text': full_text,
            'metadata': {
                'word_count': word_count,
                'character_count': character_count,
                'line_count': len(transcript_lines),
                'original_format': 'csv'
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'CSV parsing error: {str(e)}',
            'text': '',
            'metadata': {}
        }


def clean_transcript_text(text: str) -> str:
    """
    Clean transcript text by removing unnecessary elements.
    
    Args:
        text: Raw transcript text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ''
    
    # Remove common Teams transcript artifacts
    cleaned = text
    
    # Remove timestamps (various formats)
    timestamp_patterns = [
        r'\d{1,2}:\d{2}:\d{2}\.?\d*',  # HH:MM:SS or HH:MM:SS.mmm
        r'\[\d{1,2}:\d{2}:\d{2}\]',   # [HH:MM:SS]
        r'\(\d{1,2}:\d{2}:\d{2}\)',   # (HH:MM:SS)
    ]
    
    for pattern in timestamp_patterns:
        cleaned = re.sub(pattern, '', cleaned)
    
    # Remove speaker labels (simple patterns)
    speaker_patterns = [
        r'^[A-Za-z\s]+:\s*',  # Speaker Name:
        r'^[A-Za-z\s]+\s*>>\s*',  # Speaker Name >>
    ]
    
    lines = cleaned.split('\n')
    processed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Apply speaker pattern removal
        for pattern in speaker_patterns:
            line = re.sub(pattern, '', line, flags=re.MULTILINE)
        
        # Remove extra whitespace
        line = re.sub(r'\s+', ' ', line).strip()
        
        if line:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)


def extract_speakers(text: str) -> List[str]:
    """
    Extract unique speaker names from transcript text.
    
    Args:
        text: Transcript text
        
    Returns:
        List of unique speaker names
    """
    speakers = set()
    
    # Pattern to match speaker names
    speaker_patterns = [
        r'^([A-Za-z\s]+):\s*',  # Speaker Name:
        r'^([A-Za-z\s]+)\s*>>\s*',  # Speaker Name >>
    ]
    
    lines = text.split('\n')
    for line in lines:
        for pattern in speaker_patterns:
            match = re.match(pattern, line.strip())
            if match:
                speaker_name = match.group(1).strip()
                if speaker_name and len(speaker_name) > 1:
                    speakers.add(speaker_name)
    
    return sorted(list(speakers))