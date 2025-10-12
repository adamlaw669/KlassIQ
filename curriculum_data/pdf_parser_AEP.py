import fitz  # PyMuPDF
import os
import re
import json
from pathlib import Path

# === CONFIGURATION ===
PDF_FOLDER = r".\pdfs\aep_curriculum_pdfs"
OUTPUT_JSON = "AEP_master_curriculum.json"


def parse_curriculum_pdf(pdf_path):
    """
    Parses AEP curriculum PDFs (English, Math, Science, etc.)
    into a structured JSON-like dictionary.

    Works with PDFs that follow the NERDC curriculum layout
    — with columns for topic, objectives, content, teacher/pupil activities, etc.
    """
    doc = fitz.open(pdf_path)
    curriculum_data = {
        "subject": None,
        "level": None,
        "grades": {}
    }

    # --- Extract subject and level from filename ---
    filename = os.path.basename(pdf_path)
    subject_match = re.search(r"AEP\s*(.*?)\s*Level", filename, re.IGNORECASE)
    level_match = re.search(r"Level\s*(\d+)", filename, re.IGNORECASE)

    if subject_match:
        curriculum_data["subject"] = subject_match.group(1).strip().title()
    if level_match:
        curriculum_data["level"] = f"Level {level_match.group(1)}"

    current_grade = ""
    current_theme = ""
    current_sub_theme = ""
    current_topic_data = {}

    # --- Process each page ---
    for page_num, page in enumerate(doc, start=1):
        try:
            blocks = page.get_text("dict", flags=11)["blocks"]
            page_text = page.get_text().upper()

            # Identify grade (e.g. PRIMARY 1)
            grade_match = re.search(r"PRIMARY\s*([1-6])", page_text)
            if grade_match:
                current_grade = f"Primary {grade_match.group(1)}"
                if current_grade not in curriculum_data["grades"]:
                    curriculum_data["grades"][current_grade] = {"themes": []}

            # Identify theme
            theme_match = re.search(r"THEME[:\s]*(.*)", page_text)
            if theme_match:
                new_theme = theme_match.group(1).strip().title()
                if new_theme and new_theme != current_theme:
                    current_theme = new_theme
                    curriculum_data["grades"][current_grade]["themes"].append({
                        "theme_name": current_theme,
                        "sub_themes": []
                    })

            # Identify sub-theme
            sub_theme_match = re.search(r"SUB\s*THEME[:\s]*(.*)", page_text)
            if sub_theme_match:
                new_sub_theme = sub_theme_match.group(1).strip().title()
                if new_sub_theme and new_sub_theme != current_sub_theme:
                    current_sub_theme = new_sub_theme
                    current_theme_obj = curriculum_data["grades"][current_grade]["themes"][-1]
                    current_theme_obj["sub_themes"].append({
                        "sub_theme_name": current_sub_theme,
                        "topics": []
                    })

            # Column boundaries (approximate; adjust if layout shifts)
            column_boundaries = {
                "topic": (30, 120),
                "performance_objectives": (120, 250),
                "content": (250, 360),
                "activities_teacher": (360, 470),
                "activities_pupils": (470, 580),
                "resources": (580, 690),
                "evaluation": (690, 820)
            }

            # Reference to last sub-theme object
            try:
                current_sub_theme_obj = (
                    curriculum_data["grades"][current_grade]["themes"][-1]["sub_themes"][-1]
                )
            except (KeyError, IndexError):
                continue

            # Process each text span
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        x0 = span["bbox"][0]

                        if not text or text.upper() in ["TOPIC", "CONTENT", "TEACHER", "PUPILS"]:
                            continue

                        # Start new topic
                        if column_boundaries["topic"][0] <= x0 < column_boundaries["topic"][1] and len(text) > 3:
                            if current_topic_data:
                                current_sub_theme_obj["topics"].append(current_topic_data)

                            current_topic_data = {
                                "topic_name": text,
                                "performance_objectives": [],
                                "content": [],
                                "activities": {"teacher": [], "pupils": []},
                                "resources": [],
                                "evaluation": []
                            }

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
                                current_topic_data["resources"].append(text)
                            elif column_boundaries["evaluation"][0] <= x0 < column_boundaries["evaluation"][1]:
                                current_topic_data["evaluation"].append(text)
        except Exception as e:
            print(f"⚠️ Error parsing page {page_num} in {pdf_path}: {e}")
            continue

    # Append last topic
    try:
        if current_topic_data:
            current_sub_theme_obj["topics"].append(current_topic_data)
    except Exception:
        pass

    return curriculum_data


def save_to_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {output_path}")


def process_all_pdfs():
    """Processes all PDFs in the configured folder."""
    all_results = []
    pdf_files = list(Path(PDF_FOLDER).glob("*.pdf"))

    for pdf_file in pdf_files:
        print(f"📘 Processing: {pdf_file.name}")
        try:
            parsed_data = parse_curriculum_pdf(str(pdf_file))
            all_results.append(parsed_data)
        except Exception as e:
            print(f"⚠️ Error processing {pdf_file.name}: {e}")

    save_to_json(all_results, OUTPUT_JSON)
    print(f"\n🎯 Extraction complete! {len(all_results)} PDFs processed.")
    print(f"📂 Output: {OUTPUT_JSON}")


if __name__ == "__main__":
    process_all_pdfs()
