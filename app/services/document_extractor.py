"""
Document data extraction service.
Extracts structured data from documents using ChatGPT.
"""
import io
import json
import logging
import uuid
from typing import Dict, Any, Optional

import sqlalchemy.orm
from sqlalchemy.orm import Session
from PIL import Image
import pytesseract
import pdf2image
import openai

from app.db.session import SessionLocal
from app.models.document import Document
from app.services.s3_service import S3Service
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class DocumentExtractor:
    """
    Service for extracting data from documents using ChatGPT.
    
    Attributes:
        db: Database session
        s3_service: S3 service for downloading documents
    """
    
    def __init__(self, db: Session):
        """
        Initialize document extractor.
        
        Args:
            db: Database session
        """
        self.db = db
        self.s3_service = S3Service()
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image_bytes: Image data
            
        Returns:
            Extracted text
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Run OCR
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text from a PDF using OCR.
        
        Args:
            pdf_bytes: PDF data
            
        Returns:
            Extracted text
        """
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_bytes(pdf_bytes)
            
            # Extract text from each image
            extracted_text = []
            for image in images:
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format or 'JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Extract text from image
                text = self.extract_text_from_image(img_byte_arr)
                extracted_text.append(text)
            
            return "\n\n".join(extracted_text)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_structured_data_with_chatgpt(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Extract structured data from text using ChatGPT.
        
        Args:
            text: Text to extract data from
            document_type: Type of document (passport, id_card, etc.)
            
        Returns:
            Structured data extracted from text
        """
        try:
            # Create prompt based on document type
            prompt = self._get_extraction_prompt(document_type, text)
            
            # Call ChatGPT API
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a document analysis assistant that extracts structured information from documents. Return ONLY valid JSON with the extracted fields."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic output
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            # Ensure the result is valid JSON
            structured_data = json.loads(result_text)
            return structured_data
        except Exception as e:
            logger.error(f"Error extracting structured data with ChatGPT: {e}")
            return {"error": str(e)}
    
    def _get_extraction_prompt(self, document_type: str, text: str) -> str:
        """
        Get extraction prompt based on document type.
        
        Args:
            document_type: Type of document
            text: Text to extract data from
            
        Returns:
            Prompt for ChatGPT
        """
        base_prompt = f"Extract structured information from the following {document_type}. Return a JSON object with the extracted data.\n\nDocument Text:\n{text}\n\n"
        
        # Add specific fields to extract based on document type
        if document_type == "passport":
            base_prompt += """
            Extract and return the following fields in a JSON object:
            - full_name: The full name of the passport holder
            - passport_number: The passport number
            - nationality: The nationality of the holder
            - date_of_birth: The date of birth in YYYY-MM-DD format
            - place_of_birth: The place of birth
            - gender: The gender of the holder
            - issue_date: When the passport was issued in YYYY-MM-DD format
            - expiry_date: When the passport expires in YYYY-MM-DD format
            - issuing_authority: The authority that issued the passport
            """
        elif document_type == "id_card":
            base_prompt += """
            Extract and return the following fields in a JSON object:
            - full_name: The full name on the ID card
            - id_number: The ID card number
            - date_of_birth: The date of birth in YYYY-MM-DD format
            - address: The address on the ID card
            - issue_date: When the ID was issued in YYYY-MM-DD format
            - expiry_date: When the ID expires in YYYY-MM-DD format
            - issuing_authority: The authority that issued the ID card
            """
        elif document_type == "utility_bill":
            base_prompt += """
            Extract and return the following fields in a JSON object:
            - account_holder: The name of the account holder
            - account_number: The account or customer number
            - service_provider: The utility company name
            - service_type: Type of utility (electricity, water, gas, etc.)
            - billing_date: The date of the bill in YYYY-MM-DD format
            - due_date: Payment due date in YYYY-MM-DD format
            - billing_period: The period covered by the bill
            - amount_due: The amount due, as a number
            - address: The service address
            """
        elif document_type == "business_registration":
            base_prompt += """
            Extract and return the following fields in a JSON object:
            - business_name: The registered name of the business
            - registration_number: The business registration number
            - business_type: The type of business entity
            - registration_date: The date of registration in YYYY-MM-DD format
            - registered_address: The registered address of the business
            - directors: An array of director names
            - business_activity: The described business activity
            - registration_authority: The authority that issued the registration
            """
        elif document_type == "bank_statement":
            base_prompt += """
            Extract and return the following fields in a JSON object:
            - account_holder: The name of the account holder
            - account_number: The bank account number
            - bank_name: The name of the bank
            - statement_period: The period covered by the statement
            - opening_balance: The opening balance, as a number
            - closing_balance: The closing balance, as a number
            - transactions: A summary of transactions (not every transaction)
            - address: The account holder's address
            """
        else:
            # Generic document extraction
            base_prompt += """
            Extract and return all relevant fields you can identify in a JSON object.
            Include names, dates, numbers, addresses, and any other important information.
            """
        
        return base_prompt


def extract_document_data(document_id: uuid.UUID) -> None:
    """
    Background task to extract data from a document.
    
    Args:
        document_id: ID of the document to process
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        # Get document from S3
        s3_service = S3Service()
        
        try:
            # Download document
            s3_response = s3_service.s3_client.get_object(
                Bucket=s3_service.bucket_name,
                Key=document.s3_key
            )
            file_content = s3_response['Body'].read()
            
            # Extract text based on file type
            extractor = DocumentExtractor(db)
            if document.content_type.startswith('image/'):
                text = extractor.extract_text_from_image(file_content)
            elif document.content_type == 'application/pdf':
                text = extractor.extract_text_from_pdf(file_content)
            else:
                logger.error(f"Unsupported file type: {document.content_type}")
                document.is_processed = True
                document.extracted_data = {"error": "Unsupported file type"}
                db.commit()
                return
            
            # Extract structured data with ChatGPT
            structured_data = extractor.extract_structured_data_with_chatgpt(text, document.document_type)
            
            # Update document in database
            document.is_processed = True
            document.extracted_data = structured_data
            db.commit()
            logger.info(f"Successfully extracted data from document {document_id}")
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            document.is_processed = True
            document.extracted_data = {"error": str(e)}
            db.commit()
    finally:
        db.close()