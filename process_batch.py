import os
import glob
from pdf_parser import parse_atr
from database_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    folder_path = "c:/Work/CPGRAMS/Success Stories/Automation/output"
    db_manager = DatabaseManager()
    
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files.")
    
    success_count = 0
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        grievance = parse_atr(pdf_path, filename)
        
        if grievance:
            db_manager.insert_grievance(grievance)
            logger.info(f"Saved: {grievance.registration_number}")
            success_count += 1
            
    logger.info(f"Batch processing complete. Processed {success_count}/{len(pdf_files)} files.")

if __name__ == "__main__":
    main()
