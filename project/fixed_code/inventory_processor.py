"""
Inventory Processor Module

This module provides the main functionality for processing inventory files.
It handles reading, validating, transforming, and preparing inventory data for upload.
"""

import pandas as pd
import numpy as np
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from data_validator import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inventory_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('inventory_processor')


class InventoryProcessor:
    """
    Class for processing inventory files and preparing them for upload.
    """
    
    def __init__(self):
        """Initialize the inventory processor with a data validator."""
        self.validator = DataValidator()
    
    def read_inventory_file(self, file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Read an inventory file and return a DataFrame.
        
        Args:
            file_path: Path to the inventory file
            
        Returns:
            Tuple containing:
                - DataFrame with inventory data (or None if error)
                - Error message (or None if successful)
        """
        try:
            # Check file extension to determine how to read it
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif ext.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                error_msg = f"Unsupported file format: {ext}"
                logger.error(error_msg)
                return None, error_msg
            
            # Check if DataFrame is empty
            if df.empty:
                error_msg = "The inventory file is empty"
                logger.error(error_msg)
                return None, error_msg
            
            logger.info(f"Successfully read inventory file: {file_path}")
            return df, None
            
        except Exception as e:
            error_msg = f"Error reading inventory file: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def process_inventory(self, file_path: str) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Process an inventory file by reading, validating, and transforming the data.
        
        Args:
            file_path: Path to the inventory file
            
        Returns:
            Tuple containing:
                - Processed DataFrame (or None if processing failed)
                - Dictionary with processing results and validation issues
        """
        results = {
            'success': False,
            'validation_passed': False,
            'validation_issues': {},
            'error_message': None,
            'records_processed': 0,
            'records_with_issues': 0
        }
        
        # Read the inventory file
        df, error = self.read_inventory_file(file_path)
        if error:
            results['error_message'] = error
            return None, results
        
        # Store the original record count
        original_count = len(df)
        results['records_processed'] = original_count
        
        # Clean column names
        df = self.validator.clean_column_names(df)
        
        # Validate the data
        validation_passed, validation_issues = self.validator.validate_data(df)
        results['validation_passed'] = validation_passed
        results['validation_issues'] = validation_issues
        
        # Count records with issues
        records_with_issues = set()
        for issue_type, issues in validation_issues.items():
            if issue_type == 'missing_values':
                for issue in issues:
                    records_with_issues.update(issue['rows'])
            elif issue_type == 'data_type_issues':
                for issue in issues:
                    records_with_issues.update(issue['rows'])
            elif issue_type == 'price_below_cost':
                records_with_issues.update(issues)
            elif issue_type == 'special_character_issues':
                for issue in issues:
                    records_with_issues.update(issue['rows'])
        
        results['records_with_issues'] = len(records_with_issues)
        
        # Convert data types
        df = self.validator.convert_data_types(df)
        
        # Fix missing values in non-critical fields
        df = self.fix_missing_values(df)
        
        # Generate validation report
        validation_report = self.validator.generate_validation_report(validation_issues, df)
        results['validation_report'] = validation_report
        
        # Set success flag
        results['success'] = True
        
        return df, results
    
    def fix_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fix missing values in the DataFrame.
        
        Args:
            df: DataFrame with missing values
            
        Returns:
            DataFrame with fixed missing values
        """
        # Create a copy to avoid modifying the original DataFrame
        fixed_df = df.copy()
        
        # For Drivetrain Type, fill missing values with 'Unknown'
        if 'Drivetrain Type' in fixed_df.columns:
            fixed_df['Drivetrain Type'] = fixed_df['Drivetrain Type'].fillna('Unknown')
        
        # Don't fill missing values for Price as it's a critical field
        # that should be manually reviewed
        
        # For J.D. Power fields, fill with the median value if numeric
        for col in ['J.D. Power Trade In', 'J.D. Power Retail Clean']:
            if col in fixed_df.columns:
                if pd.api.types.is_numeric_dtype(fixed_df[col]):
                    median_value = fixed_df[col].median()
                    fixed_df[col] = fixed_df[col].fillna(median_value)
        
        return fixed_df
    
    def save_processed_inventory(self, df: pd.DataFrame, output_path: str) -> bool:
        """
        Save the processed inventory DataFrame to a file.
        
        Args:
            df: Processed DataFrame
            output_path: Path to save the processed file
            
        Returns:
            Boolean indicating if the save was successful
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save based on file extension
            _, ext = os.path.splitext(output_path)
            
            if ext.lower() in ['.xlsx', '.xls']:
                df.to_excel(output_path, index=False)
            elif ext.lower() == '.csv':
                df.to_csv(output_path, index=False)
            else:
                logger.error(f"Unsupported output format: {ext}")
                return False
            
            logger.info(f"Successfully saved processed inventory to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving processed inventory: {str(e)}")
            return False
    
    def generate_summary_report(self, results: Dict[str, Any], output_path: str) -> bool:
        """
        Generate a summary report of the processing results.
        
        Args:
            results: Dictionary with processing results
            output_path: Path to save the summary report
            
        Returns:
            Boolean indicating if the report generation was successful
        """
        try:
            # Create the report content
            report = "# Inventory Processing Summary Report\n\n"
            
            # Add processing status
            report += f"## Processing Status\n"
            report += f"- Success: {'Yes' if results['success'] else 'No'}\n"
            if results['error_message']:
                report += f"- Error: {results['error_message']}\n"
            report += f"- Records Processed: {results['records_processed']}\n"
            report += f"- Records with Issues: {results['records_with_issues']}\n\n"
            
            # Add validation status
            report += f"## Validation Status\n"
            report += f"- Validation Passed: {'Yes' if results['validation_passed'] else 'No'}\n\n"
            
            # Add validation issues summary
            if 'validation_issues' in results:
                report += f"## Validation Issues Summary\n"
                for issue_type, issues in results['validation_issues'].items():
                    if issues:
                        report += f"- {issue_type.replace('_', ' ').title()}: {len(issues)} issues\n"
                report += "\n"
            
            # Add detailed validation report if available
            if 'validation_report' in results:
                report += results['validation_report']
            
            # Write the report to file
            with open(output_path, 'w') as f:
                f.write(report)
            
            logger.info(f"Successfully generated summary report: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating summary report: {str(e)}")
            return False