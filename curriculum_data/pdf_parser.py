import fitz  # PyMuPDF
import json
import re

def parse_curriculum_pdf(pdf_path):
    """
    Parses the Nigerian curriculum PDF and converts it into a structured JSON format.

    This parser is specifically designed for the layout of 'pri1-3_basic_science_technology.pdf'.
    """
    doc = fitz.open(pdf_path)
    curriculum_data = {}

    # this are to track were we arey
    current_grade = ""
    current_theme = ""
    current_sub_theme = ""
    current_topic_data = {}

    for page_num, page in enumerate(doc):
        # Extract text blocks with their coordinates
        blocks = page.get_text("dict", flags=11)["blocks"]

        # --- 1. Identify Headers (Grade, Theme, Sub-theme) ---
        page_text = page.get_text().upper() # Get all text for easy searching
        
        # Find Grade (e.g., "PRIMARY 1")
        grade_match = re.search(r"PRIMARY\s*([1-3])", page_text)
        if grade_match:
            current_grade = f"Primary {grade_match.group(1)}"
            if current_grade not in curriculum_data:
                curriculum_data[current_grade] = {"themes": []}

        # Find Theme
        theme_match = re.search(r"THEME:\s*(.*)", page_text)
        if theme_match:
            new_theme = theme_match.group(1).strip().title()
            if new_theme != current_theme:
                current_theme = new_theme
                print(current_theme)
                curriculum_data[current_grade]["themes"].append({
                    "theme_name": current_theme,
                    "sub_themes": []
                })

        # Find Sub-theme
        sub_theme_match = re.search(r"SUB\s*THEME:\s*(.*)", page_text)
        if sub_theme_match:
            new_sub_theme = sub_theme_match.group(1).strip().title()
            if new_sub_theme != current_sub_theme:
                current_sub_theme = new_sub_theme
                # Find the current theme object to append to
                for theme_obj in curriculum_data[current_grade]["themes"]:
                    if theme_obj["theme_name"] == current_theme:
                        theme_obj["sub_themes"].append({
                            "sub_theme_name": current_sub_theme,
                            "topics": []
                        })
                        break
        
        # --- 2. Identify Table Structure and Content ---
        # Define approximate horizontal (x-coordinate) boundaries for each column
        # These values were found by inspecting the PDF layout.
        column_boundaries = {
            "topic": (30, 120),
            "performance_objectives": (120, 250),
            "content": (250, 360),
            "activities_teacher": (360, 470),
            "activities_pupils": (470, 580),
            "resources": (580, 690),
            "evaluation": (690, 800)
        }

        # Find the last sub_theme object to add topics to
        try:
            current_sub_theme_obj = curriculum_data[current_grade]["themes"][-1]["sub_themes"][-1]
        except (KeyError, IndexError):
            continue # Skip pages without a defined theme/sub-theme yet

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        x0 = span["bbox"][0] # Left x-coordinate
                        
                        # Skip empty text or table headers
                        if not text or text.upper() in ["TOPIC", "CONTENT", "TEACHER", "PUPILS"]:
                            continue

                        # Is this a new topic?
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
    
    # Append the very last topic being processed
    if current_topic_data:
        current_sub_theme_obj["topics"].append(current_topic_data)

    return curriculum_data

def save_to_json(data, output_filename):
    """Saves dictionary data to a JSON file."""
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Successfully saved data to {output_filename}")


if __name__ == "__main__":
    pdf_file = ".\p_1_3_curriculum_pdfs\pri1-3_basic_science_technology.pdf"
    json_output_file = "curriculum_output.json"
    
    parsed_data = parse_curriculum_pdf(pdf_file)
    
    if parsed_data:
        save_to_json(parsed_data, json_output_file)