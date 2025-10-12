import fitz  # PyMuPDF
import json
import re
import os # For path manipulation

def parse_and_save_curriculum_pdf_to_json(pdf_path, output_dir=".", output_filename=None):
    """
    Parses a Nigerian curriculum PDF and converts it into a structured JSON format.
    It then saves this structured data to a JSON file.

    Args:
        pdf_path (str): The file path to the input PDF curriculum document.
        output_dir (str, optional): The directory where the JSON file will be saved.
                                    Defaults to the current directory (".").
        output_filename (str, optional): The desired name for the output JSON file.
                                         If None, a name will be inferred from the PDF filename.

    Returns:
        dict: The parsed curriculum data as a dictionary if successful, None otherwise.
    """
    doc = fitz.open(pdf_path)
    
    # Try to infer subject from filename for metadata and default output filename
    filename = os.path.basename(pdf_path).lower()
    base_name_without_ext = os.path.splitext(filename)[0]
    
    subject_match = re.search(r"pri[1-3]-(.*?)$", base_name_without_ext) # Regex now matches till end of basename
    subject = "Unknown Subject"
    if subject_match:
        # Basic cleaning for subject name
        subject = subject_match.group(1).replace('_', ' ').title()
        if 'Basic Science Technology' in subject:
            subject = 'Basic Science & Technology'
        elif 'English Studies' in subject:
            subject = 'English Studies'
        # Add more specific subject mapping here if needed
    
    # Set default output filename if not provided
    if output_filename is None:
        output_filename = f"{base_name_without_ext}_structured.json"
    
    # Construct the full output path
    full_output_path = os.path.join(output_dir, output_filename)

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # The main data structure to hold all parsed curriculum data
    curriculum_all_grades_data = {
        "curriculum_title": f"{subject} Curriculum (Primary 1-3)", # Dynamic title
        "subject": subject,
        "grades": [] # This will be a list of grade objects
    }
    
    # State tracking variables (now storing dict objects)
    current_grade_obj = None     # Points to the current grade's dict in curriculum_all_grades_data["grades"]
    current_theme_obj = None     # Points to the current theme's dict in current_grade_obj["themes"]
    current_sub_theme_obj = None # Points to the current sub-theme's dict in current_theme_obj["sub_themes"]
    current_topic_data = {}      # The dict for the topic currently being built

    # Define approximate horizontal (x-coordinate) boundaries for each column
    # IMPORTANT: These values are derived from your screenshot/original script.
    # They might need fine-tuning for other PDFs if column alignments differ.
    column_boundaries = {
        "topic": (30, 120),
        "performance_objectives": (120, 250),
        "content": (250, 360),
        "activities_teacher": (360, 470),
        "activities_pupils": (470, 580),
        "resources": (580, 690),
        "evaluation": (690, 800)
    }

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", flags=11)["blocks"]
        page_text_upper = page.get_text().upper() # Get all text for easy searching

        # --- 1. Identify and Update Headers (Grade, Theme, Sub-theme) ---

        # Find Grade (e.g., "PRIMARY 1", "PRIMARY 2", "PRIMARY 3")
        # Assuming grade declaration is a significant event that resets theme/sub-theme context
        grade_match = re.search(r"PRIMARY\s*([1-3])", page_text_upper)
        if grade_match:
            new_grade_level_str = f"Primary {grade_match.group(1)}"
            
            # Check if this is a new grade or a transition to a different existing grade
            if not current_grade_obj or current_grade_obj.get("grade_level") != new_grade_level_str:
                # If we're transitioning from one grade to another,
                # finalize the last topic of the previous context (if any)
                if current_topic_data and current_sub_theme_obj:
                    current_sub_theme_obj["topics"].append(current_topic_data)
                    current_topic_data = {} # Reset topic data for the new context

                # Try to find an existing grade object, or create a new one
                found_grade = False
                for g_obj in curriculum_all_grades_data["grades"]:
                    if g_obj["grade_level"] == new_grade_level_str:
                        current_grade_obj = g_obj
                        found_grade = True
                        break
                
                if not found_grade:
                    current_grade_obj = {"grade_level": new_grade_level_str, "themes": []}
                    curriculum_all_grades_data["grades"].append(current_grade_obj)
                
                # Reset theme and sub-theme context since grade has changed
                current_theme_obj = None
                current_sub_theme_obj = None
        
        # Ensure we have a current_grade_obj before proceeding with themes/sub-themes/topics
        if not current_grade_obj:
            # print(f"Warning: No grade found on page {page_num}. Skipping content.")
            continue # Skip pages until a grade is identified

        # Find Theme
        theme_match = re.search(r"THEME:\s*(.*)", page_text_upper)
        if theme_match:
            new_theme_name = theme_match.group(1).strip().title()
            if not current_theme_obj or current_theme_obj.get("theme_name") != new_theme_name:
                # Finalize last topic/sub-theme if theme is changing
                if current_topic_data and current_sub_theme_obj:
                    current_sub_theme_obj["topics"].append(current_topic_data)
                    current_topic_data = {}

                # Try to find an existing theme object within the current grade, or create a new one
                found_theme = False
                for t_obj in current_grade_obj["themes"]:
                    if t_obj["theme_name"] == new_theme_name:
                        current_theme_obj = t_obj
                        found_theme = True
                        break
                
                if not found_theme:
                    current_theme_obj = {"theme_name": new_theme_name, "sub_themes": []}
                    current_grade_obj["themes"].append(current_theme_obj)
                
                # Reset sub-theme context since theme has changed
                current_sub_theme_obj = None

        if not current_theme_obj:
            # print(f"Warning: No theme found for grade {current_grade_obj['grade_level']} on page {page_num}. Skipping content.")
            continue

        # Find Sub-theme
        sub_theme_match = re.search(r"SUB\s*THEME:\s*(.*)", page_text_upper)
        if sub_theme_match:
            new_sub_theme_name = sub_theme_match.group(1).strip().title()
            if not current_sub_theme_obj or current_sub_theme_obj.get("sub_theme_name") != new_sub_theme_name:
                # Finalize last topic if sub-theme is changing
                if current_topic_data and current_sub_theme_obj:
                    current_sub_theme_obj["topics"].append(current_topic_data)
                    current_topic_data = {}

                # Try to find an existing sub-theme object within the current theme, or create a new one
                found_sub_theme = False
                for st_obj in current_theme_obj["sub_themes"]:
                    if st_obj["sub_theme_name"] == new_sub_theme_name:
                        current_sub_theme_obj = st_obj
                        found_sub_theme = True
                        break
                
                if not found_sub_theme:
                    current_sub_theme_obj = {"sub_theme_name": new_sub_theme_name, "topics": []}
                    current_theme_obj["sub_themes"].append(current_sub_theme_obj)
        
        if not current_sub_theme_obj:
            # print(f"Warning: No sub-theme found for theme {current_theme_obj['theme_name']} on page {page_num}. Skipping content.")
            continue

        # --- 2. Identify Table Structure and Content ---
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        x0 = span["bbox"][0] # Left x-coordinate
                        
                        # Skip empty text or table headers (case-insensitive check)
                        if not text or text.upper() in ["TOPIC / SKILLS", "TOPIC", "OBJECTIVES", "CONTENTS", 
                                                        "ACTIVITIES", "TEACHER", "PUPILS", 
                                                        "TEACHING AND LEARNING RESOURCES", "EVALUATION GUIDE"]:
                            continue

                        # Is this a new topic? (Check x-coordinate and text length for validity)
                        if column_boundaries["topic"][0] <= x0 < column_boundaries["topic"][1] and len(text) > 3:
                            # If there was a previous topic being built, save it first
                            if current_topic_data:
                                current_sub_theme_obj["topics"].append(current_topic_data)

                            # Start a new topic
                            current_topic_data = {
                                "topic_name": text,
                                "performance_objectives": [],
                                "content": [],
                                "activities": {"teacher": [], "pupils": []},
                                "teaching_and_learning_resources": [],
                                "evaluation_guide": []
                            }
                        
                        # Add content to the current topic based on column
                        # Ensure current_topic_data exists before attempting to append
                        elif current_topic_data:
                            if column_boundaries["performance_objectives"][0] <= x0 < column_boundaries["performance_objectives"][1]:
                                current_topic_data["performance_objectives"].append(text)
                            elif column_boundaries["content"][0] <= x0 < column_boundaries["content"][1]:
                                current_topic_data["content"].append(text)
                            elif column_boundaries["activities_teacher"][0] <= x0 < column_boundaries["activities_teacher"][1]:
                                current_topic_data["activities"]["teacher"].append(text)
                            elif column_boundaries["activities_pupils"][0] <= x0 < column_boundaries["activities_pupils"][1]:
                                current_topic_data["activities"]["pupils"].append(text)
                            elif column_boundaries["resources"][0] <= x0 < column_boundaries["resources"][1]:
                                current_topic_data["teaching_and_learning_resources"].append(text)
                            elif column_boundaries["evaluation"][0] <= x0 < column_boundaries["evaluation"][1]:
                                current_topic_data["evaluation_guide"].append(text)
    
    # --- Finalization ---
    # Append the very last topic being processed after the loop finishes
    if current_topic_data and current_sub_theme_obj:
        current_sub_theme_obj["topics"].append(current_topic_data)

    # Save the data to a JSON file
    if curriculum_all_grades_data["grades"]:
        try:
            with open(full_output_path, 'w', encoding='utf-8') as f:
                json.dump(curriculum_all_grades_data, f, indent=2)
            print(f"✅ Successfully parsed and saved data to {full_output_path}")
            return curriculum_all_grades_data
        except IOError as e:
            print(f"❌ Error saving JSON to {full_output_path}: {e}")
            return None
    else:
        print(f"❌ No valid curriculum data parsed or grades found for {pdf_path}.")
        return None

# --- Example Usage (for testing purposes) ---
if __name__ == "__main__":
    # Define your PDF file path
    pdf_file_to_parse = ".\p_1_3_curriculum_pdfs\pri1-3_basic_science_technology.pdf" 
    
    # Define the output directory (e.g., a 'data' folder)
    output_directory = "./parsed_curriculum_data"

    # You can also specify a custom output filename if you don't want the inferred one
    # custom_output_name = "my_science_curriculum.json"

    # Call the combined function
    parsed_data = parse_and_save_curriculum_pdf_to_json(
        pdf_path=pdf_file_to_parse, 
        output_dir=output_directory,
        # output_filename=custom_output_name # Uncomment to use a custom name
    )
    
    if parsed_data:
        print(f"Parsed data (first few themes): {parsed_data['grades'][0]['themes'][:2] if parsed_data['grades'] else 'No grades found'}")