"""
Test Script for Inventory Upload Solution

This script tests the implemented solution with both problematic and correct inventory files.
"""

import os
import sys
import pandas as pd
from data_validator import DataValidator
from inventory_processor import InventoryProcessor
from upload_handler import UploadHandler

def test_solution():
    """Test the inventory upload solution with test files."""
    print("=== Testing Inventory Upload Solution ===\n")
    
    # Create test output directory
    test_output_dir = "../analysis/test_results"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Initialize components
    validator = DataValidator()
    processor = InventoryProcessor()
    handler = UploadHandler()
    
    # Test with problematic inventory file
    print("Testing with problematic inventory file...")
    problematic_file = "../data/problematic_inventory/problematic_inventory.xlsx"
    problematic_output_dir = os.path.join(test_output_dir, "problematic")
    os.makedirs(problematic_output_dir, exist_ok=True)
    
    problematic_results = handler.handle_upload_process(
        problematic_file, 
        problematic_output_dir,
        {
            'skip_records_with_issues': True,
            'save_processed_file': True,
            'save_results': True
        }
    )
    
    print(f"Problematic file processing success: {problematic_results['success']}")
    print(f"Validation passed: {problematic_results['validation_passed']}")
    print(f"Records processed: {problematic_results['records_processed']}")
    print(f"Records with issues: {problematic_results['records_with_issues']}")
    if 'records_uploaded' in problematic_results:
        print(f"Records uploaded: {problematic_results['records_uploaded']}")
    print()
    
    # Test with correct inventory file
    print("Testing with correct inventory file...")
    correct_file = "../data/sample_inventory/correct_inventory.xlsx"
    correct_output_dir = os.path.join(test_output_dir, "correct")
    os.makedirs(correct_output_dir, exist_ok=True)
    
    correct_results = handler.handle_upload_process(
        correct_file, 
        correct_output_dir,
        {
            'skip_records_with_issues': True,
            'save_processed_file': True,
            'save_results': True
        }
    )
    
    print(f"Correct file processing success: {correct_results['success']}")
    print(f"Validation passed: {correct_results['validation_passed']}")
    print(f"Records processed: {correct_results['records_processed']}")
    print(f"Records with issues: {correct_results['records_with_issues']}")
    if 'records_uploaded' in correct_results:
        print(f"Records uploaded: {correct_results['records_uploaded']}")
    print()
    
    # Compare results
    print("=== Comparison of Results ===")
    print(f"Problematic file validation passed: {problematic_results['validation_passed']}")
    print(f"Correct file validation passed: {correct_results['validation_passed']}")
    
    if 'records_uploaded' in problematic_results and 'records_uploaded' in correct_results:
        problematic_upload_rate = problematic_results['records_uploaded'] / problematic_results['records_processed'] * 100
        correct_upload_rate = correct_results['records_uploaded'] / correct_results['records_processed'] * 100
        
        print(f"Problematic file upload rate: {problematic_upload_rate:.2f}%")
        print(f"Correct file upload rate: {correct_upload_rate:.2f}%")
    
    print("\n=== Test Complete ===")
    
    return {
        'problematic_results': problematic_results,
        'correct_results': correct_results
    }

if __name__ == "__main__":
    test_solution()