"""
Character Bible Parser V2
Extracts structured data from the updated Saving Nora Character Bible document (v2)
Specifically designed for the new format with "CHARACTER 3: HENRY SMITH" format
"""

import docx
import json
import os
import re
from typing import Dict, List, Any, Optional


def clean_text(text: str) -> str:
    """Clean text of special characters and normalize whitespace."""
    if not text:
        return ""
    # Replace various unicode characters
    text = text.replace('\u2013', '-').replace('\u2014', '-')
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2022', '•')
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.strip()


def is_character_header(para) -> Optional[str]:
    """Check if paragraph is a character header (Heading 1 style with 'CHARACTER' prefix)."""
    if para.style and para.style.name == 'Heading 1':
        text = clean_text(para.text).upper()
        # Check for "CHARACTER 3: HENRY SMITH" format
        if text.startswith("CHARACTER") and "HENRY SMITH" in text:
            return "HENRY SMITH"
    return None


def is_section_header(para) -> Optional[str]:
    """Check if paragraph is a section header (Heading 2 style)."""
    if para.style and para.style.name == 'Heading 2':
        text = clean_text(para.text)
        # Sections start with numbers like "1. ", "2. ", etc. (with period, not parenthesis)
        if re.match(r'^\d+\.\s+', text):
            return text
    return None


def is_subsection_header(para) -> Optional[str]:
    """Check if paragraph is a subsection header (Heading 3 style)."""
    if para.style and para.style.name == 'Heading 3':
        return clean_text(para.text)
    return None


def extract_key_value(text: str) -> Optional[tuple]:
    """Extract key-value pairs from text like 'Name: value'."""
    if ':' in text:
        parts = text.split(':', 1)
        key = clean_text(parts[0])
        value = clean_text(parts[1])
        # Only treat as key-value if key is reasonably short (not a full sentence)
        if len(key) < 80 and value:
            return (key, value)
    return None


def parse_character_bible_v2(docx_path: str, character_name: str = "HENRY SMITH") -> Dict[str, Any]:
    """
    Parse the character bible document v2 and extract structured data for specified character.
    
    Args:
        docx_path: Path to the .docx file
        character_name: Name of character to extract (default: "HENRY SMITH")
    
    Returns:
        Dictionary with character data
    """
    doc = docx.Document(docx_path)
    
    character_data: Dict[str, Any] = {
        'meta': {
            'name': character_name,
            'source': os.path.basename(docx_path),
            'scope': 'EP001-100'
        }
    }
    
    current_section: Optional[str] = None
    current_subsection: Optional[str] = None
    content_buffer: List[str] = []
    found_character = False
    
    def flush_buffer():
        """Flush accumulated content to the appropriate location."""
        nonlocal content_buffer, current_section, current_subsection
        
        if not content_buffer or not current_section:
            return
        
        content = '\n'.join(content_buffer).strip()
        if not content:
            content_buffer = []
            return
        
        # Determine where to store the content
        if current_subsection:
            # Store in subsection
            if current_subsection not in character_data[current_section]:
                character_data[current_section][current_subsection] = content
            else:
                # Append if already exists
                character_data[current_section][current_subsection] += "\n\n" + content
        elif current_section:
            # Store as section content
            if 'content' not in character_data[current_section]:
                character_data[current_section]['content'] = []
            character_data[current_section]['content'].append(content)
        
        content_buffer = []
    
    # Process all paragraphs
    for para in doc.paragraphs:
        text = clean_text(para.text)
        
        # Skip empty paragraphs
        if not text:
            continue
        
        # Check for character header
        char_name = is_character_header(para)
        if char_name and char_name == character_name:
            found_character = True
            flush_buffer()
            current_section = None
            current_subsection = None
            continue
        
        # If we found the character, start processing
        if not found_character:
            continue
        
        # If we hit another character header, stop processing
        if para.style and para.style.name == 'Heading 1' and char_name and char_name != character_name:
            break
        
        # Check for section header
        section_name = is_section_header(para)
        if section_name:
            flush_buffer()
            current_section = section_name
            current_subsection = None
            
            if current_section not in character_data:
                character_data[current_section] = {}
            continue
        
        # Check for subsection header (Heading 3)
        subsection_name = is_subsection_header(para)
        if subsection_name:
            flush_buffer()
            current_subsection = subsection_name
            
            if current_section and current_subsection not in character_data[current_section]:
                character_data[current_section][current_subsection] = ""
            continue
        
        # Process content within a section
        if current_section:
            # Try to extract key-value pair
            kv = extract_key_value(text)
            if kv:
                flush_buffer()
                key, value = kv
                # Store as direct key-value in section
                if key not in character_data[current_section]:
                    character_data[current_section][key] = value
                else:
                    # Append if key already exists
                    character_data[current_section][key] += "\n" + value
            else:
                # Check if this looks like a subsection label (short text, no period, followed by content)
                # For example: "Vocabulary Level" followed by content
                if len(text) < 50 and not text.endswith('.') and not text.endswith(':') and not ':' in text:
                    # Check if next paragraph has content - if so, this might be a subsection
                    # For now, just accumulate
                    content_buffer.append(text)
                else:
                    # Accumulate as content
                    content_buffer.append(text)
    
    # Flush any remaining buffer
    flush_buffer()
    
    if not found_character:
        print(f"Warning: Character '{character_name}' not found in document")
    
    return character_data


def save_character_to_json(character_data: Dict[str, Any], output_dir: str, character_name: str):
    """Save character data to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create safe filename
    safe_name = character_name.replace(" ", "_").lower()
    file_path = os.path.join(output_dir, f"{safe_name}_updated.json")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(character_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved: {file_path}")
    return file_path


def main():
    """Main execution function."""
    docx_path = "PromoCanon/Saving_Nora_CHARACTER_BIBLE_2.docx"
    output_dir = "context/characters"
    character_name = "HENRY SMITH"
    
    if not os.path.exists(docx_path):
        print(f"Error: File not found: {docx_path}")
        return
    
    print(f"Parsing: {docx_path}")
    print(f"Extracting: {character_name}")
    print("=" * 60)
    
    character_data = parse_character_bible_v2(docx_path, character_name)
    
    print(f"\nExtracted sections for {character_name}:")
    for section_name in character_data.keys():
        if section_name != 'meta':
            print(f"  - {section_name}")
    
    print("\nSaving to JSON file...")
    save_character_to_json(character_data, output_dir, character_name)
    
    print("\n" + "=" * 60)
    print("Parsing complete!")


if __name__ == "__main__":
    main()
