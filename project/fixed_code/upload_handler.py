"""
Upload Handler Module

This module provides functionality for handling the upload process of inventory data.
It ensures that data is properly validated and formatted before upload.
"""

import pandas as pd
import numpy as np
import os
import logging
import json
from typing import Dict, List, Tuple, Any, Optional
from data_validator import DataValidator
from inventory_processor import InventoryProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('upload_handler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('upload_handler')


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(JSONEncoder, self).default(obj)


class UploadHandler:
    """
    Class for handling the upload process of inventory data.
    """
    
    def __init__(self):
        """Initialize the upload handler with an inventory processor."""
        self.processor = InventoryProcessor()
        self.validator = DataValidator()
    
    def prepare_for_upload(self, file_path: str) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Prepare inventory data for upload by processing and validating it.
        
        Args:
            file_path: Path to the inventory file
            
        Returns:
            Tuple containing:
                - DataFrame ready for upload (or None if preparation failed)
                - Dictionary with preparation results
        """
        # Process the inventory file
        df, results = self.processor.process_inventory(file_path)
        
        # If processing failed, return the results
        if not results['success']:
            return None, results
        
        # If validation failed, mark records with issues
        if not results['validation_passed']:
            df = self.mark_records_with_issues(df, results['validation_issues'])
        
        # Prepare the data for upload
        df = self.format_for_upload(df)
        
        return df, results
    
    def mark_records_with_issues(self, df: pd.DataFrame, validation_issues: Dict[str, List[Any]]) -> pd.DataFrame:
        """
        Mark records with validation issues for review.
        
        Args:
            df: DataFrame with inventory data
            validation_issues: Dictionary with validation issues
            
        Returns:
            DataFrame with marked records
        """
        # Create a copy to avoid modifying the original DataFrame
        marked_df = df.copy()
        
        # Add columns to indicate if the record has issues
        marked_df['has_issues'] = False
        marked_df['issue_type'] = ''  # Initialize as empty string
        
        # Mark records with missing values
        for issue in validation_issues.get('missing_values', []):
            for row in issue['rows']:
                marked_df.loc[row, 'has_issues'] = True
                marked_df.loc[row, 'issue_type'] = marked_df.loc[row, 'issue_type'] + f"Missing {issue['field']}; "
        
        # Mark records with data type issues
        for issue in validation_issues.get('data_type_issues', []):
            for row in issue['rows']:
                marked_df.loc[row, 'has_issues'] = True
                marked_df.loc[row, 'issue_type'] = marked_df.loc[row, 'issue_type'] + f"Invalid {issue['field']} format; "
        
        # Mark records with price below cost
        for row in validation_issues.get('price_below_cost', []):
            marked_df.loc[row, 'has_issues'] = True
            marked_df.loc[row, 'issue_type'] = marked_df.loc[row, 'issue_type'] + "Price below cost; "
        
        # Mark records with special character issues
        for issue in validation_issues.get('special_character_issues', []):
            for row in issue['rows']:
                marked_df.loc[row, 'has_issues'] = True
                marked_df.loc[row, 'issue_type'] = marked_df.loc[row, 'issue_type'] + f"Special characters in {issue['field']}; "
        
        return marked_df
    
    def format_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format the DataFrame for upload by ensuring proper data types and structure.
        
        Args:
            df: DataFrame with inventory data
            
        Returns:
            Formatted DataFrame ready for upload
        """
        # Create a copy to avoid modifying the original DataFrame
        formatted_df = df.copy()
        
        # Ensure all column names are clean (no newlines, consistent format)
        formatted_df.columns = [col.replace('\n', ' ') for col in formatted_df.columns]
        
        # Convert numeric columns to appropriate types
        numeric_columns = ['Year', 'Odometer', 'Price', 'Unit Cost', 'J.D. Power Trade In', 'J.D. Power Retail Clean']
        for col in numeric_columns:
            if col in formatted_df.columns:
                formatted_df[col] = pd.to_numeric(formatted_df[col], errors='coerce')
        
        # Ensure VIN is a string
        if 'VIN' in formatted_df.columns:
            formatted_df['VIN'] = formatted_df['VIN'].astype(str)
        
        # Clean up any special characters in text fields
        text_columns = ['Make', 'Model', 'Series', 'Class', 'Engine', 'Body', 'Transmission']
        for col in text_columns:
            if col in formatted_df.columns:
                # Replace any problematic characters with spaces
                formatted_df[col] = formatted_df[col].astype(str).str.replace(r'[^\w\s,.-]', ' ', regex=True)
        
        return formatted_df
    
    def upload_inventory(self, df: pd.DataFrame, upload_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload the inventory data to the system.
        
        Note: This is a placeholder method that would be implemented to interface
        with the actual upload API or system. For now, it simulates the upload process.
        
        Args:
            df: DataFrame with inventory data ready for upload
            upload_config: Dictionary with upload configuration
            
        Returns:
            Dictionary with upload results
        """
        # This is a placeholder for the actual upload implementation
        # In a real system, this would connect to an API or database
        
        results = {
            'success': False,
            'records_uploaded': 0,
            'records_failed': 0,
            'error_message': None
        }
        
        try:
            # Filter out records with issues if specified in config
            if upload_config.get('skip_records_with_issues', True):
                if 'has_issues' in df.columns:
                    clean_df = df[~df['has_issues']]
                    skipped_count = len(df) - len(clean_df)
                    logger.info(f"Skipped {skipped_count} records with issues")
                else:
                    clean_df = df
            else:
                clean_df = df
            
            # Simulate the upload process
            # In a real implementation, this would call an API or database
            logger.info(f"Uploading {len(clean_df)} records...")
            
            # Simulate successful upload
            results['success'] = True
            results['records_uploaded'] = int(len(clean_df))  # Convert to standard Python int
            results['records_failed'] = 0
            
            logger.info(f"Successfully uploaded {len(clean_df)} records")
            
        except Exception as e:
            error_msg = f"Error during upload: {str(e)}"
            logger.error(error_msg)
            results['error_message'] = error_msg
            results['records_failed'] = len(df)
        
        return results
    
    def save_upload_results(self, results: Dict[str, Any], output_path: str) -> bool:
        """
        Save the upload results to a file.
        
        Args:
            results: Dictionary with upload results
            output_path: Path to save the results
            
        Returns:
            Boolean indicating if the save was successful
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the results as JSON using the custom encoder
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, cls=JSONEncoder)
            
            logger.info(f"Successfully saved upload results to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving upload results: {str(e)}")
            return False
    
    def handle_upload_process(self, file_path: str, output_dir: str, upload_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle the complete upload process from file to system.
        
        Args:
            file_path: Path to the inventory file
            output_dir: Directory to save output files
            upload_config: Dictionary with upload configuration (optional)
            
        Returns:
            Dictionary with process results
        """
        # Set default upload configuration if not provided
        if upload_config is None:
            upload_config = {
                'skip_records_with_issues': True,
                'save_processed_file': True,
                'save_results': True
            }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare the data for upload
        df, prep_results = self.prepare_for_upload(file_path)
        
        # If preparation failed, return the results
        if df is None:
            return prep_results
        
        # Save the processed file if specified
        if upload_config.get('save_processed_file', True):
            processed_path = os.path.join(output_dir, 'processed_inventory.xlsx')
            self.processor.save_processed_inventory(df, processed_path)
        
        # Upload the data
        upload_results = self.upload_inventory(df, upload_config)
        
        # Combine preparation and upload results
        combined_results = {**prep_results, **upload_results}
        
        # Save the results if specified
        if upload_config.get('save_results', True):
            results_path = os.path.join(output_dir, 'upload_results.json')
            self.save_upload_results(combined_results, results_path)
            
            # Generate and save summary report
            report_path = os.path.join(output_dir, 'upload_summary.md')
            self.processor.generate_summary_report(combined_results, report_path)
        
        return combined_results