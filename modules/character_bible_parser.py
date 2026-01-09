"""
Character Bible Parser
Extracts structured data from the Saving Nora Character Bible document
and saves it as JSON files in the context folder.
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
    """Check if paragraph is a character header (Heading 1 style)."""
    if para.style and para.style.name == 'Heading 1':
        text = clean_text(para.text).upper()
        # Known characters
        known_chars = ["NORA SMITH", "JUSTIN HUNT", "HENRY SMITH"]
        if text in known_chars:
            return text
    return None


def is_section_header(para) -> Optional[str]:
    """Check if paragraph is a section header (Heading 2 style)."""
    if para.style and para.style.name == 'Heading 2':
        text = clean_text(para.text)
        # Sections start with numbers like "1) ", "2) ", etc.
        if re.match(r'^\d+\)\s+', text):
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


def parse_character_bible(docx_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Parse the character bible document and extract structured data.
    
    Returns a dictionary with character names as keys and their data as values.
    """
    doc = docx.Document(docx_path)
    
    characters: Dict[str, Dict[str, Any]] = {}
    current_char: Optional[str] = None
    current_section: Optional[str] = None
    current_subsection: Optional[str] = None
    content_buffer: List[str] = []
    
    def flush_buffer():
        """Flush accumulated content to the appropriate location."""
        nonlocal content_buffer, current_char, current_section, current_subsection
        
        if not content_buffer or not current_char:
            return
        
        content = '\n'.join(content_buffer).strip()
        if not content:
            content_buffer = []
            return
        
        # Determine where to store the content
        if current_subsection:
            # Store in subsection
            if current_subsection not in characters[current_char][current_section]:
                characters[current_char][current_section][current_subsection] = content
            else:
                # Append if already exists
                characters[current_char][current_section][current_subsection] += "\n\n" + content
        elif current_section:
            # Store as section content
            if 'content' not in characters[current_char][current_section]:
                characters[current_char][current_section]['content'] = []
            characters[current_char][current_section]['content'].append(content)
        
        content_buffer = []
    
    # Process all paragraphs
    for para in doc.paragraphs:
        text = clean_text(para.text)
        
        # Skip empty paragraphs
        if not text:
            continue
        
        # Check for character header
        char_name = is_character_header(para)
        if char_name:
            flush_buffer()
            current_char = char_name
            current_section = None
            current_subsection = None
            
            if current_char not in characters:
                characters[current_char] = {
                    'meta': {
                        'name': current_char,
                        'source': os.path.basename(docx_path),
                        'scope': 'EP001-100'
                    }
                }
            continue
        
        # Only process content if we have a current character
        if not current_char:
            continue
        
        # Check for section header
        section_name = is_section_header(para)
        if section_name:
            flush_buffer()
            current_section = section_name
            current_subsection = None
            
            if current_section not in characters[current_char]:
                characters[current_char][current_section] = {}
            continue
        
        # Check for subsection header
        subsection_name = is_subsection_header(para)
        if subsection_name:
            flush_buffer()
            current_subsection = subsection_name
            
            if current_section and current_subsection not in characters[current_char][current_section]:
                characters[current_char][current_section][current_subsection] = ""
            continue
        
        # Process content within a section
        if current_section:
            # Try to extract key-value pair
            kv = extract_key_value(text)
            if kv:
                flush_buffer()
                key, value = kv
                # Store as direct key-value in section
                if key not in characters[current_char][current_section]:
                    characters[current_char][current_section][key] = value
                else:
                    # Append if key already exists
                    characters[current_char][current_section][key] += "\n" + value
            else:
                # Accumulate as content
                content_buffer.append(text)
    
    # Flush any remaining buffer
    flush_buffer()
    
    return characters


def save_characters_to_json(characters: Dict[str, Any], output_dir: str):
    """Save character data to individual JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    
    for char_name, char_data in characters.items():
        # Create safe filename
        safe_name = char_name.replace(" ", "_").lower()
        file_path = os.path.join(output_dir, f"{safe_name}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(char_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved: {file_path}")
    
    # Also save a combined file
    combined_path = os.path.join(output_dir, "all_characters.json")
    with open(combined_path, 'w', encoding='utf-8') as f:
        json.dump(characters, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {combined_path}")


def main():
    """Main execution function."""
    docx_path = "PromoCanon/Saving_Nora_CHARACTER BIBLE.docx"
    output_dir = "context/characters"
    
    if not os.path.exists(docx_path):
        print(f"Error: File not found: {docx_path}")
        return
    
    print(f"Parsing: {docx_path}")
    print("=" * 60)
    
    characters = parse_character_bible(docx_path, output_dir)
    
    print(f"\nExtracted {len(characters)} characters:")
    for char_name in characters.keys():
        print(f"  - {char_name}")
    
    print("\nSaving to JSON files...")
    save_characters_to_json(characters, output_dir)
    
    print("\n" + "=" * 60)
    print("Parsing complete!")


if __name__ == "__main__":
    main()
