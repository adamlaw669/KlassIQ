#!/usr/bin/env python3
"""
Merge all class-level curriculum JSON files into one centralized curriculum_map.json.

This script iterates through all curriculum folders (parsed_pri1_3_curr_json, 
parsed_pri4_6_curr_json, parsed_js_curr_json) and merges every subject JSON 
into a single hierarchical structure.

Author: KlassIQ Backend Team
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def validate_json_structure(data: Dict[str, Any]) -> bool:
    """
    Validate that the curriculum JSON follows the expected nested structure.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        bool: True if valid structure, False otherwise
    """
    try:
        # Check if it's a dictionary
        if not isinstance(data, dict):
            return False
            
        # Each level (e.g., "PRIMARY 1", "JSS1") should have THEMES
        for level_name, level_data in data.items():
            if not isinstance(level_data, dict):
                continue
                
            if "THEMES" not in level_data:
                logger.warning(f"Level {level_name} missing THEMES")
                continue
                
            themes = level_data["THEMES"]
            if not isinstance(themes, list):
                logger.warning(f"Level {level_name} THEMES is not a list")
                continue
                
            # Validate theme structure
            for theme in themes:
                if not isinstance(theme, dict):
                    continue
                    
                if "THEME NAME" not in theme or "SUB THEMES" not in theme:
                    logger.warning(f"Theme in {level_name} missing required keys")
                    continue
                    
        return True
    except Exception as e:
        logger.error(f"Error validating JSON structure: {e}")
        return False


def load_subject_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load and validate a subject JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dict containing the subject data or None if invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if validate_json_structure(data):
            logger.info(f"Successfully loaded {file_path.name}")
            return data
        else:
            logger.warning(f"Invalid structure in {file_path.name}")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path.name}: {e}")
        return None


def merge_curriculums() -> Dict[str, Any]:
    """
    Main function to merge all curriculum JSON files into a single structure.
    
    Returns:
        Dict: Merged curriculum structure
    """
    # Define the curriculum structure and folder mappings
    curriculum_levels = {
        "Primary 1–3": "parsed_pri1_3_curr_json",
        "Primary 4–6": "parsed_pri4_6_curr_json", 
        "Junior Secondary 1–3": "parsed_js_curr_json"
    }
    
    # Get the base curriculum data path
    base_path = Path(__file__).resolve().parents[2] / "curriculum_data" / "parsed_jsons"
    
    if not base_path.exists():
        raise FileNotFoundError(f"Curriculum data path not found: {base_path}")
    
    merged_curriculum = {}
    
    # Process each level
    for level_name, folder_name in curriculum_levels.items():
        folder_path = base_path / folder_name
        
        if not folder_path.exists():
            logger.warning(f"Folder not found: {folder_path}")
            continue
            
        logger.info(f"Processing {level_name} from {folder_name}")
        merged_curriculum[level_name] = {}
        
        # Process all JSON files in the folder
        json_files = list(folder_path.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files in {folder_name}")
        
        for json_file in json_files:
            # Extract subject name from filename (remove .json extension)
            subject_name = json_file.stem
            
            # Skip if already exists (shouldn't happen, but safety check)
            if subject_name in merged_curriculum[level_name]:
                logger.warning(f"Subject {subject_name} already exists in {level_name}")
                continue
                
            # Load the subject data
            subject_data = load_subject_json(json_file)
            if subject_data is not None:
                merged_curriculum[level_name][subject_name] = subject_data
                logger.info(f"Added {subject_name} to {level_name}")
            else:
                logger.error(f"Failed to load {subject_name} from {json_file}")
    
    return merged_curriculum


def save_merged_curriculum(merged_data: Dict[str, Any], output_path: Path) -> bool:
    """
    Save the merged curriculum to JSON file with validation.
    
    Args:
        merged_data: The merged curriculum dictionary
        output_path: Path where to save the merged JSON
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate the merged structure
        if not merged_data:
            logger.error("Merged data is empty")
            return False
            
        # Save with pretty formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2, sort_keys=True)
            
        logger.info(f"Successfully saved merged curriculum to {output_path}")
        
        # Log statistics
        total_subjects = sum(len(subjects) for subjects in merged_data.values())
        logger.info(f"Merged curriculum contains {len(merged_data)} levels and {total_subjects} subjects")
        
        for level_name, subjects in merged_data.items():
            logger.info(f"  {level_name}: {len(subjects)} subjects")
            
        return True
        
    except Exception as e:
        logger.error(f"Error saving merged curriculum: {e}")
        return False


def main():
    """Main entry point for the script."""
    try:
        logger.info("Starting curriculum merge process...")
        
        # Merge all curriculums
        merged_curriculum = merge_curriculums()
        
        if not merged_curriculum:
            logger.error("No curriculum data was merged")
            return False
            
        # Define output path
        output_path = Path(__file__).resolve().parents[1] / "data" / "curriculum_map.json"
        
        # Save the merged curriculum
        success = save_merged_curriculum(merged_curriculum, output_path)
        
        if success:
            logger.info("Curriculum merge completed successfully!")
            return True
        else:
            logger.error("Failed to save merged curriculum")
            return False
            
    except Exception as e:
        logger.error(f"Fatal error during merge process: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)