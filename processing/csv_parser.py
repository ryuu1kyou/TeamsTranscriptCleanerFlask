"""
CSV parser service for Flask application.
"""
import csv
import io
from typing import List, Dict


def parse_csv_text(csv_text: str) -> List[Dict[str, str]]:
    """
    Parse word correction list from CSV text.

    Args:
        csv_text: CSV format text

    Returns:
        Word correction list [{"incorrect": "word", "correct": "word"}, ...]
    """
    result = []

    try:
        # Process string as CSV
        csv_file = io.StringIO(csv_text)
        reader = csv.reader(csv_file)

        # Skip header row
        header = next(reader, None)

        # Process each row
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                result.append({
                    "incorrect": row[0].strip(),
                    "correct": row[1].strip()
                })
    except Exception as e:
        print(f"Error occurred while parsing CSV text: {e}")
        # Return empty list if error occurs
        return []

    return result


def validate_csv_format(csv_text: str) -> List[str]:
    """
    Validate CSV format and return list of errors.

    Args:
        csv_text: CSV format text

    Returns:
        List of validation error messages
    """
    errors = []
    
    if not csv_text.strip():
        errors.append("CSV content cannot be empty")
        return errors

    try:
        csv_file = io.StringIO(csv_text)
        reader = csv.reader(csv_file)
        
        # Check header
        header = next(reader, None)
        if not header or len(header) < 2:
            errors.append("CSV must have at least 2 columns")
        
        row_count = 0
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 2:
                errors.append(f"Row {row_num}: Must have at least 2 columns")
            elif not row[0].strip() or not row[1].strip():
                errors.append(f"Row {row_num}: Both columns must have values")
            row_count += 1
        
        if row_count == 0:
            errors.append("CSV must contain at least one data row")
            
    except Exception as e:
        errors.append(f"CSV parsing error: {str(e)}")
    
    return errors


def csv_to_dict_list(csv_text: str, columns: List[str] = None) -> List[Dict[str, str]]:
    """
    Convert CSV text to list of dictionaries.

    Args:
        csv_text: CSV format text
        columns: List of column names (if None, uses first row as header)

    Returns:
        List of dictionaries
    """
    result = []
    
    try:
        csv_file = io.StringIO(csv_text)
        reader = csv.reader(csv_file)
        
        if columns:
            headers = columns
        else:
            headers = next(reader, None)
            
        if not headers:
            return result
            
        for row in reader:
            if len(row) >= len(headers):
                row_dict = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row[i].strip() if i < len(row) else ""
                result.append(row_dict)
                
    except Exception as e:
        print(f"Error converting CSV to dict list: {e}")
        
    return result


def format_csv_content(word_pairs: List[Dict[str, str]]) -> str:
    """
    Format word pairs as CSV content.

    Args:
        word_pairs: List of word correction pairs

    Returns:
        CSV formatted string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['incorrect', 'correct'])
    
    # Write data rows
    for pair in word_pairs:
        writer.writerow([pair.get('incorrect', ''), pair.get('correct', '')])
    
    return output.getvalue()