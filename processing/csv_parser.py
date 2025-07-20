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
