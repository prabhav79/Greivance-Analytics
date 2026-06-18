import re
from docling_parser import extract_structured_text
from database_manager import Grievance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_field(text, label_pattern, end_pattern=r'\n'):
    """
    Extracts text between a label pattern and an end pattern.
    """
    regex = rf"{label_pattern}\s*[:\-]?\s*(.*?)(?={end_pattern})"
    match = re.search(regex, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def parse_atr(pdf_path, pdf_filename):
    logger.info(f"Parsing {pdf_filename}...")
    try:
        # Use docling for structured extraction (layout-aware, cached)
        full_text = extract_structured_text(pdf_path)
            
        # Basic cleanup
        # full_text = re.sub(r'\s+', ' ', full_text) # Flatten whitespace might help or hurt depending on layout
        
        # Extract Registration Number
        # "Grievance Details for registration number : DOAAC/I/2024/0000150"
        reg_num = extract_field(full_text, r"registration number", r"\n|Name")
        if not reg_num:
            # Fallback try
            reg_match = re.search(r"([A-Z]+/[A-Z]/\d{4}/\d+)", full_text)
            if reg_match:
                reg_num = reg_match.group(1)
        
        name = extract_field(full_text, r"Name", r"Date of receipt")
        date_of_receipt = extract_field(full_text, r"Date of receipt", r"Address")
        district = extract_field(full_text, r"District name", r"State name")
        state = extract_field(full_text, r"State name", r"Mobile no")
        mobile = extract_field(full_text, r"Mobile no", r"Email Id")
        email = extract_field(full_text, r"Email Id", r"Grievance description")
        
        # Description
        # Usually between "Grievance description" and the next section or EOF
        # But there might be other sections like "Action Taken Report" later.
        desc_match = re.search(r"Grievance description\s*(.*?)(?=(Current Status|Grievance Document|Officer Details|$))", full_text, re.IGNORECASE | re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else None
        
        # Status
        status = "Unknown"
        if "Disposed" in full_text:
            status = "Disposed"
        elif "Closed" in full_text:
            status = "Closed"
            
        # Action Taken
        # This is harder as it might be labeled differently or just appear at the end.
        # Often it is under "Remarks" or "Action Taken"
        action_taken = None
        action_match = re.search(r"(Action Taken|Remarks)\s*[:\-]?\s*(.*)", full_text, re.IGNORECASE | re.DOTALL)
        if action_match:
            action_taken = action_match.group(2).strip()
            
        return Grievance(
            registration_number=reg_num or "UNKNOWN",
            name=name,
            date_of_receipt=date_of_receipt,
            district=district,
            state=state,
            mobile=mobile,
            email=email,
            description=description,
            status=status,
            action_taken=action_taken,
            full_text=full_text,
            pdf_filename=pdf_filename
        )
    except Exception as e:
        logger.error(f"Failed to parse {pdf_filename}: {e}")
        return None
