"""
Data Validator Module

This module provides functions for validating inventory data before processing.
It checks for common issues identified in the error analysis:
- Missing values in critical fields
- Data format inconsistencies
- Price and cost inconsistencies
- Special characters and newline characters
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Any, Optional


class DataValidator:
    """
    Class for validating inventory data and identifying issues.
    """
    
    def __init__(self):
        # Define required fields for validation
        self.required_fields = [
            'Year', 'Stock #', 'VIN', 'Make', 'Model', 'Price', 'Unit Cost'
        ]
        
        # Define expected data types for each column
        self.expected_types = {
            'Year': 'int',
            'Odometer': 'int',
            'Price': 'numeric',
            'Unit Cost': 'numeric',
            'J.D. Power\nTrade In': 'numeric',
            'J.D. Power\nRetail Clean': 'numeric'
        }
        
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, List[Any]]]:
        """
        Validate the inventory data and return validation results.
        
        Args:
            df: DataFrame containing inventory data
            
        Returns:
            Tuple containing:
                - Boolean indicating if validation passed
                - Dictionary with validation issues
        """
        issues = {
            'missing_values': [],
            'data_type_issues': [],
            'price_below_cost': [],
            'column_name_issues': [],
            'special_character_issues': []
        }
        
        # Check for missing values in required fields
        for field in self.required_fields:
            if field in df.columns:
                missing_count = df[field].isnull().sum()
                if missing_count > 0:
                    issues['missing_values'].append({
                        'field': field,
                        'count': missing_count,
                        'rows': df[df[field].isnull()].index.tolist()
                    })
        
        # Check for data type issues
        for col, expected_type in self.expected_types.items():
            if col in df.columns:
                if expected_type == 'int':
                    # Check if values can be converted to integers
                    non_int_mask = ~df[col].isnull() & df[col].astype(str).str.match(r'^-?\d+$').eq(False)
                    if non_int_mask.any():
                        issues['data_type_issues'].append({
                            'field': col,
                            'expected_type': expected_type,
                            'rows': df[non_int_mask].index.tolist()
                        })
                elif expected_type == 'numeric':
                    # Check if values can be converted to float
                    try:
                        pd.to_numeric(df[col], errors='raise')
                    except ValueError:
                        non_numeric_mask = ~df[col].isnull() & pd.to_numeric(df[col], errors='coerce').isnull()
                        issues['data_type_issues'].append({
                            'field': col,
                            'expected_type': expected_type,
                            'rows': df[non_numeric_mask].index.tolist()
                        })
        
        # Check for price below cost
        if 'Price' in df.columns and 'Unit Cost' in df.columns:
            # Convert to numeric to ensure proper comparison
            price = pd.to_numeric(df['Price'], errors='coerce')
            cost = pd.to_numeric(df['Unit Cost'], errors='coerce')
            
            # Find rows where price is less than cost
            price_below_cost_mask = (price < cost) & ~price.isnull() & ~cost.isnull()
            if price_below_cost_mask.any():
                issues['price_below_cost'] = df[price_below_cost_mask].index.tolist()
        
        # Check for newline characters in column names
        for col in df.columns:
            if '\n' in col:
                issues['column_name_issues'].append(col)
        
        # Check for special characters in the Class field
        if 'Class' in df.columns:
            special_char_pattern = r'[^a-zA-Z0-9\s,]'
            rows_with_special_chars = df[df['Class'].str.contains(special_char_pattern, regex=True, na=False)].index.tolist()
            if rows_with_special_chars:
                issues['special_character_issues'].append({
                    'field': 'Class',
                    'rows': rows_with_special_chars
                })
        
        # Determine if validation passed
        validation_passed = all(len(issue_list) == 0 for issue_list in issues.values())
        
        return validation_passed, issues
    
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean column names by removing newline characters and standardizing format.
        
        Args:
            df: DataFrame with original column names
            
        Returns:
            DataFrame with cleaned column names
        """
        # Create a copy to avoid modifying the original DataFrame
        cleaned_df = df.copy()
        
        # Create a mapping of old column names to new column names
        column_mapping = {}
        for col in cleaned_df.columns:
            # Replace newline characters with spaces
            new_col = col.replace('\n', ' ')
            column_mapping[col] = new_col
        
        # Rename the columns
        cleaned_df = cleaned_df.rename(columns=column_mapping)
        
        return cleaned_df
    
    def convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert columns to their expected data types.
        
        Args:
            df: DataFrame with columns to convert
            
        Returns:
            DataFrame with converted data types
        """
        # Create a copy to avoid modifying the original DataFrame
        converted_df = df.copy()
        
        # Convert columns to their expected types
        for col, expected_type in self.expected_types.items():
            if col in converted_df.columns:
                if expected_type == 'int':
                    # Convert to integer, coercing errors to NaN
                    converted_df[col] = pd.to_numeric(converted_df[col], errors='coerce')
                    # Convert NaN to None for proper handling
                    converted_df[col] = converted_df[col].astype('Int64')
                elif expected_type == 'numeric':
                    # Convert to float, coercing errors to NaN
                    converted_df[col] = pd.to_numeric(converted_df[col], errors='coerce')
        
        return converted_df
    
    def generate_validation_report(self, validation_results: Dict[str, List[Any]], df: pd.DataFrame) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            validation_results: Dictionary with validation issues
            df: Original DataFrame
            
        Returns:
            String containing the validation report
        """
        report = "# Inventory Data Validation Report\n\n"
        
        # Add summary
        total_issues = sum(len(issues) for issues in validation_results.values())
        report += f"## Summary\n"
        report += f"- Total records: {len(df)}\n"
        report += f"- Total issues found: {total_issues}\n\n"
        
        # Add details for each issue type
        if validation_results['missing_values']:
            report += "## Missing Values\n"
            for issue in validation_results['missing_values']:
                report += f"- Field '{issue['field']}' has {issue['count']} missing values (rows: {issue['rows']})\n"
            report += "\n"
        
        if validation_results['data_type_issues']:
            report += "## Data Type Issues\n"
            for issue in validation_results['data_type_issues']:
                report += f"- Field '{issue['field']}' has values that cannot be converted to {issue['expected_type']} (rows: {issue['rows']})\n"
            report += "\n"
        
        if validation_results['price_below_cost']:
            report += "## Price Below Cost\n"
            report += f"- {len(validation_results['price_below_cost'])} records have Price less than Unit Cost (rows: {validation_results['price_below_cost']})\n\n"
        
        if validation_results['column_name_issues']:
            report += "## Column Name Issues\n"
            report += f"- {len(validation_results['column_name_issues'])} columns have newline characters: {validation_results['column_name_issues']}\n\n"
        
        if validation_results['special_character_issues']:
            report += "## Special Character Issues\n"
            for issue in validation_results['special_character_issues']:
                report += f"- Field '{issue['field']}' has special characters in {len(issue['rows'])} rows (rows: {issue['rows']})\n"
            report += "\n"
        
        return report