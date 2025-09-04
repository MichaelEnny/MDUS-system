"""
Test Document Generator
Generate varied test documents for comprehensive testing
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class TestDocumentGenerator:
    """Generate test documents with varied characteristics"""
    
    def __init__(self, output_dir: str = "test_documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.document_metadata = []
        
        # Set random seed for reproducible test documents
        random.seed(42)
        np.random.seed(42)
    
    def generate_text_image(self, text: str, width: int = 800, height: int = 600, 
                           font_size: int = 20, text_color: str = 'black',
                           bg_color: str = 'white') -> Image.Image:
        """Generate an image with text content"""
        
        image = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(image)
        
        # Try to use a default font, fallback to built-in if not available
        try:
            # This will work on most systems
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        # Split text into lines that fit the image width
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            # Estimate text width (approximate)
            if len(test_line) * (font_size * 0.6) < width - 40:  # 40px margin
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Draw text lines
        y_offset = 20
        line_height = font_size + 5
        
        for line in lines:
            if y_offset + line_height > height - 20:  # Bottom margin
                break
            draw.text((20, y_offset), line, fill=text_color, font=font)
            y_offset += line_height
        
        return image
    
    def generate_form_image(self, form_data: Dict[str, str], 
                           width: int = 800, height: int = 600) -> Image.Image:
        """Generate a form-like document image"""
        
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        # Draw form title
        title = "MEDICAL FORM"
        draw.text((width//2 - 60, 20), title, fill='black', font=font)
        
        # Draw form fields
        y_offset = 80
        field_height = 40
        
        for field_name, field_value in form_data.items():
            # Field label
            draw.text((50, y_offset), f"{field_name}:", fill='black', font=font)
            
            # Field box
            box_y = y_offset + 20
            draw.rectangle([(200, box_y), (width-50, box_y+25)], outline='black', width=1)
            
            # Field value
            if field_value:
                draw.text((210, box_y+5), field_value, fill='blue', font=font)
            
            y_offset += field_height
            
            if y_offset > height - 60:
                break
        
        return image
    
    def generate_table_image(self, data: List[List[str]], 
                           width: int = 800, height: int = 600) -> Image.Image:
        """Generate a table-like document image"""
        
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        if not data:
            return image
        
        # Calculate table dimensions
        rows = len(data)
        cols = len(data[0]) if data else 0
        
        if rows == 0 or cols == 0:
            return image
        
        cell_width = (width - 40) // cols  # 20px margin on each side
        cell_height = min(30, (height - 40) // rows)  # 20px margin top/bottom
        
        # Draw table
        start_x, start_y = 20, 20
        
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                x1 = start_x + col_idx * cell_width
                y1 = start_y + row_idx * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height
                
                # Draw cell border
                draw.rectangle([(x1, y1), (x2, y2)], outline='black', width=1)
                
                # Draw cell text
                if cell_data:
                    # Truncate text if too long
                    max_chars = cell_width // 8  # Rough estimation
                    display_text = cell_data[:max_chars] if len(cell_data) > max_chars else cell_data
                    draw.text((x1+5, y1+5), display_text, fill='black', font=font)
        
        return image
    
    def generate_test_document_set(self) -> List[Dict[str, Any]]:
        """Generate a comprehensive set of test documents"""
        
        documents = []
        
        # 1. Simple text documents
        text_samples = [
            "This is a simple medical document with basic text content. Patient information and treatment notes.",
            "MEDICAL RECORD\n\nPatient: John Doe\nDate: 2024-01-15\n\nSymptoms: Headache, fatigue\nTreatment: Rest, fluids\nFollow-up: 1 week",
            "PRESCRIPTION\n\nPatient Name: Jane Smith\nMedication: Ibuprofen 400mg\nDosage: Take twice daily with food\nQuantity: 30 tablets",
            "LAB RESULTS\n\nPatient ID: 12345\nTest Date: 2024-01-20\nBlood Pressure: 120/80\nHeart Rate: 72 bpm\nTemperature: 98.6°F"
        ]
        
        for i, text in enumerate(text_samples):
            image = self.generate_text_image(text)
            doc_info = {
                'type': 'text_document',
                'filename': f'text_document_{i+1}.png',
                'content': image,
                'expected_features': ['text_extraction', 'basic_ocr'],
                'complexity': 'low',
                'text_length': len(text)
            }
            documents.append(doc_info)
        
        # 2. Form documents
        form_samples = [
            {
                'Patient Name': 'Alice Johnson',
                'DOB': '1985-03-10',
                'Phone': '555-0123',
                'Address': '123 Main St',
                'Insurance': 'BlueCross'
            },
            {
                'Doctor': 'Dr. Smith',
                'Patient ID': 'P-789',
                'Visit Date': '2024-01-25',
                'Chief Complaint': 'Annual checkup',
                'Diagnosis': 'Healthy'
            }
        ]
        
        for i, form_data in enumerate(form_samples):
            image = self.generate_form_image(form_data)
            doc_info = {
                'type': 'form_document',
                'filename': f'form_document_{i+1}.png',
                'content': image,
                'expected_features': ['form_extraction', 'field_detection', 'structured_data'],
                'complexity': 'medium',
                'field_count': len(form_data)
            }
            documents.append(doc_info)
        
        # 3. Table documents
        table_samples = [
            [
                ['Date', 'Test', 'Result', 'Range'],
                ['2024-01-15', 'Glucose', '95', '70-100'],
                ['2024-01-15', 'Cholesterol', '180', '<200'],
                ['2024-01-15', 'BP Systolic', '120', '<120']
            ],
            [
                ['Medication', 'Dosage', 'Frequency', 'Duration'],
                ['Aspirin', '81mg', 'Daily', '30 days'],
                ['Lisinopril', '10mg', 'Daily', 'Ongoing'],
                ['Metformin', '500mg', 'Twice daily', 'Ongoing']
            ]
        ]
        
        for i, table_data in enumerate(table_samples):
            image = self.generate_table_image(table_data)
            doc_info = {
                'type': 'table_document', 
                'filename': f'table_document_{i+1}.png',
                'content': image,
                'expected_features': ['table_extraction', 'structured_data', 'row_column_detection'],
                'complexity': 'high',
                'row_count': len(table_data),
                'col_count': len(table_data[0]) if table_data else 0
            }
            documents.append(doc_info)
        
        # 4. Variation documents (different sizes, qualities, orientations)
        variations = [
            {'size': (400, 300), 'name': 'small_document'},
            {'size': (1200, 800), 'name': 'large_document'},
            {'size': (600, 800), 'name': 'portrait_document'},
            {'size': (800, 400), 'name': 'wide_document'}
        ]
        
        base_text = "MEDICAL DOCUMENT - Size and format variation test. This document tests different dimensions and formats."
        
        for i, variation in enumerate(variations):
            image = self.generate_text_image(
                base_text,
                width=variation['size'][0],
                height=variation['size'][1]
            )
            doc_info = {
                'type': 'variation_document',
                'filename': f'{variation["name"]}.png',
                'content': image,
                'expected_features': ['text_extraction', 'format_handling'],
                'complexity': 'medium',
                'width': variation['size'][0],
                'height': variation['size'][1]
            }
            documents.append(doc_info)
        
        # 5. Quality variation documents
        quality_tests = [
            {'bg_color': 'lightgray', 'text_color': 'darkblue', 'name': 'low_contrast'},
            {'bg_color': 'white', 'text_color': 'black', 'font_size': 12, 'name': 'small_text'},
            {'bg_color': 'white', 'text_color': 'black', 'font_size': 36, 'name': 'large_text'}
        ]
        
        for i, quality in enumerate(quality_tests):
            image = self.generate_text_image(
                "Quality test document with varying visual characteristics for OCR testing.",
                bg_color=quality.get('bg_color', 'white'),
                text_color=quality.get('text_color', 'black'),
                font_size=quality.get('font_size', 20)
            )
            doc_info = {
                'type': 'quality_test',
                'filename': f'quality_{quality["name"]}.png',
                'content': image,
                'expected_features': ['ocr_robustness', 'quality_handling'],
                'complexity': 'medium',
                'quality_factor': quality['name']
            }
            documents.append(doc_info)
        
        return documents
    
    def save_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Save generated documents to disk and return file paths"""
        
        saved_paths = []
        
        for doc_info in documents:
            filename = doc_info['filename']
            filepath = self.output_dir / filename
            
            # Save image
            if isinstance(doc_info['content'], Image.Image):
                doc_info['content'].save(filepath, format='PNG')
                saved_paths.append(str(filepath))
                
                # Save metadata
                metadata = {k: v for k, v in doc_info.items() if k != 'content'}
                metadata['filepath'] = str(filepath)
                metadata['file_size'] = os.path.getsize(filepath)
                
                self.document_metadata.append(metadata)
        
        # Save metadata summary
        metadata_file = self.output_dir / 'document_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(self.document_metadata, f, indent=2)
        
        logger.info(f"Generated {len(saved_paths)} test documents in {self.output_dir}")
        return saved_paths
    
    def generate_statistical_summary(self) -> Dict[str, Any]:
        """Generate statistical summary of created documents"""
        
        if not self.document_metadata:
            return {}
        
        df = pd.DataFrame(self.document_metadata)
        
        summary = {
            'total_documents': len(self.document_metadata),
            'document_types': df['type'].value_counts().to_dict(),
            'complexity_distribution': df['complexity'].value_counts().to_dict(),
            'average_file_size': df['file_size'].mean(),
            'file_size_range': {
                'min': df['file_size'].min(),
                'max': df['file_size'].max(),
                'std': df['file_size'].std()
            }
        }
        
        # Add type-specific statistics
        if 'text_length' in df.columns:
            text_docs = df[df['text_length'].notna()]
            if not text_docs.empty:
                summary['text_statistics'] = {
                    'avg_text_length': text_docs['text_length'].mean(),
                    'text_length_range': {
                        'min': text_docs['text_length'].min(),
                        'max': text_docs['text_length'].max()
                    }
                }
        
        if 'field_count' in df.columns:
            form_docs = df[df['field_count'].notna()]
            if not form_docs.empty:
                summary['form_statistics'] = {
                    'avg_field_count': form_docs['field_count'].mean(),
                    'field_count_range': {
                        'min': form_docs['field_count'].min(),
                        'max': form_docs['field_count'].max()
                    }
                }
        
        return summary

def create_test_documents(output_dir: str = "test_documents") -> Tuple[List[str], Dict[str, Any]]:
    """Create a complete set of test documents"""
    
    generator = TestDocumentGenerator(output_dir)
    documents = generator.generate_test_document_set()
    file_paths = generator.save_documents(documents)
    summary = generator.generate_statistical_summary()
    
    logger.info("Test Document Generation Summary:")
    logger.info(f"  Total documents: {summary.get('total_documents', 0)}")
    logger.info(f"  Document types: {summary.get('document_types', {})}")
    logger.info(f"  Average file size: {summary.get('average_file_size', 0):.0f} bytes")
    
    return file_paths, summary

if __name__ == "__main__":
    # Generate test documents when run directly
    file_paths, summary = create_test_documents()
    print(f"Generated {len(file_paths)} test documents")
    print(f"Summary: {json.dumps(summary, indent=2)}")