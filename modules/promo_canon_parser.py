"""
Parser module for PromoCanon markdown files.
Handles parsing of cliffhangers, characters, and episodic summaries.
Caches parsed data to JSON files for faster subsequent loads.
"""

import re
import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


class CliffhangerParser:
    """Parser for cliffhanger markdown files"""
    
    @staticmethod
    def parse_major_cliffhangers(file_path: str) -> List[Dict]:
        """
        Parse major cliffhangers from markdown file.
        
        Args:
            file_path: Path to the major cliffhangers markdown file
            
        Returns:
            List of cliffhanger dictionaries with episode, title, description, type, etc.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cliffhangers = []
        
        # Pattern to match cliffhanger sections
        pattern = r'### \*\*Episode (\d+): (.+?)\*\*\s*\n\s*\*\*Cliffhanger:\*\* (.+?)(?=\n\s*\*\*Type:|\n\s*---|\Z)'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            episode_num = int(match.group(1))
            title = match.group(2).strip()
            cliffhanger_text = match.group(3).strip()
            
            # Extract type
            type_match = re.search(r'\*\*Type:\*\* (.+?)(?=\n|$)', content[match.end():match.end()+200])
            cliffhanger_type = type_match.group(1).strip() if type_match else "Unknown"
            
            # Extract context analysis if available
            context_match = re.search(r'\*\*Context Analysis:\*\*\s*(.+?)(?=\n\s*\*\*Arc Threat:|\n\s*---|\Z)', 
                                     content[match.end():], re.DOTALL)
            context = context_match.group(1).strip() if context_match else ""
            
            # Extract arc threat
            threat_match = re.search(r'\*\*Arc Threat:\*\* (.+?)(?=\n\s*---|\Z)', 
                                    content[match.end():], re.DOTALL)
            arc_threat = threat_match.group(1).strip() if threat_match else ""
            
            cliffhangers.append({
                'episode': episode_num,
                'title': title,
                'cliffhanger_text': cliffhanger_text,
                'type': cliffhanger_type,
                'context': context,
                'arc_threat': arc_threat,
                'severity': 'major'
            })
        
        return cliffhangers
    
    @staticmethod
    def parse_minor_cliffhangers(file_path: str) -> List[Dict]:
        """
        Parse minor cliffhangers from markdown file.
        
        Args:
            file_path: Path to the minor cliffhangers markdown file
            
        Returns:
            List of cliffhanger dictionaries
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cliffhangers = []
        
        # Pattern for minor cliffhangers
        pattern = r'### \*\*Episode (\d+): (.+?)\*\*\s*\n\s*\*\*Cliffhanger:\*\* (.+?)(?=\n\s*\*\*Type:|\n\s*###|\Z)'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            episode_num = int(match.group(1))
            title = match.group(2).strip()
            cliffhanger_text = match.group(3).strip()
            
            # Extract type
            type_match = re.search(r'\*\*Type:\*\* (.+?)(?=\n|$)', content[match.end():match.end()+200])
            cliffhanger_type = type_match.group(1).strip() if type_match else "Unknown"
            
            # Extract immediate threat
            threat_match = re.search(r'\*\*Immediate Threat:\*\* (.+?)(?=\n\s*###|\Z)', 
                                    content[match.end():], re.DOTALL)
            immediate_threat = threat_match.group(1).strip() if threat_match else ""
            
            cliffhangers.append({
                'episode': episode_num,
                'title': title,
                'cliffhanger_text': cliffhanger_text,
                'type': cliffhanger_type,
                'immediate_threat': immediate_threat,
                'severity': 'minor'
            })
        
        return cliffhangers


class CharacterParser:
    """Parser for character markdown files"""
    
    @staticmethod
    def parse_characters(file_path: str) -> Dict[str, Dict]:
        """
        Parse character information from markdown file.
        
        Args:
            file_path: Path to the characters markdown file
            
        Returns:
            Dictionary mapping character names to their descriptions
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        characters = {}
        
        # Pattern to match character sections (e.g., **Nora Smith** - description)
        pattern = r'\*\*([^*]+?)\*\*\s*-\s*(.+?)(?=\n\s*\*\*|\n\s*##|\Z)'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            name = match.group(1).strip()
            description = match.group(2).strip()
            
            # Clean up description (remove extra whitespace)
            description = re.sub(r'\s+', ' ', description)
            
            characters[name] = {
                'name': name,
                'description': description
            }
        
        return characters


class EpisodicSummaryParser:
    """Parser for episodic summary markdown files"""
    
    @staticmethod
    def parse_episode_summary(file_path: str, episode_num: int) -> Optional[Dict]:
        """
        Parse a specific episode's summary from the episodic summary file.
        
        Args:
            file_path: Path to the episodic summary markdown file
            episode_num: Episode number to extract
            
        Returns:
            Dictionary with episode summary or None if not found
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match episode sections
        pattern = rf'Episode-{episode_num}\s*\n\s*# (.+?)\s*\n\s*(.+?)(?=\n\s*Episode-|\Z)'
        
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            title = match.group(1).strip()
            summary = match.group(2).strip()
            
            return {
                'episode': episode_num,
                'title': title,
                'summary': summary
            }
        
        return None
    
    @staticmethod
    def get_all_episodes(file_path: str) -> List[Dict]:
        """
        Parse all episodes from the summary file.
        
        Args:
            file_path: Path to the episodic summary markdown file
            
        Returns:
            List of episode dictionaries
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        episodes = []
        
        # Pattern to match all episode sections
        pattern = r'Episode-(\d+)\s*\n\s*# (.+?)\s*\n\s*(.+?)(?=\n\s*Episode-|\Z)'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            episode_num = int(match.group(1))
            title = match.group(2).strip()
            summary = match.group(3).strip()
            
            episodes.append({
                'episode': episode_num,
                'title': title,
                'summary': summary
            })
        
        return episodes


class PromoCanonLoader:
    """Main loader class for PromoCanon files"""
    
    def __init__(self, canon_directory: str, cache_dir: Optional[str] = None):
        """
        Initialize the loader with a PromoCanon directory.
        
        Args:
            canon_directory: Path to the PromoCanon directory containing MD files
            cache_dir: Directory to store cache files (default: .cache in canon_directory)
        """
        self.canon_dir = Path(canon_directory)
        
        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = self.canon_dir / ".cache"
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cliffhanger_parser = CliffhangerParser()
        self.character_parser = CharacterParser()
        self.summary_parser = EpisodicSummaryParser()
        
        # Cache for loaded data
        self._major_cliffhangers = None
        self._minor_cliffhangers = None
        self._characters = None
        self._episodes = None
        
        # Cache file paths
        self._cache_files = {
            'major_cliffhangers': self.cache_dir / 'major_cliffhangers.json',
            'minor_cliffhangers': self.cache_dir / 'minor_cliffhangers.json',
            'characters': self.cache_dir / 'characters.json',
            'episodes': self.cache_dir / 'episodes.json',
            'cache_metadata': self.cache_dir / 'cache_metadata.json'
        }
    
    def _get_source_file_mtime(self, filename: str) -> Optional[float]:
        """Get modification time of source file"""
        source_file = self.canon_dir / filename
        if source_file.exists():
            return os.path.getmtime(source_file)
        return None
    
    def _is_cache_valid(self, cache_file: Path, source_files: List[str]) -> bool:
        """Check if cache file is valid (exists and newer than source files)"""
        if not cache_file.exists():
            return False
        
        cache_mtime = os.path.getmtime(cache_file)
        
        # Check if any source file is newer than cache
        for source_file in source_files:
            source_mtime = self._get_source_file_mtime(source_file)
            if source_mtime and source_mtime > cache_mtime:
                return False
        
        return True
    
    def _load_from_cache(self, cache_file: Path) -> Optional[any]:
        """Load data from JSON cache file"""
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # If cache is corrupted, return None to force re-parsing
            return None
    
    def _save_to_cache(self, data: any, cache_file: Path):
        """Save data to JSON cache file"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            # If we can't write cache, continue without it
            pass
    
    def _update_cache_metadata(self):
        """Update cache metadata with current timestamp"""
        metadata = {
            'last_updated': datetime.now().isoformat(),
            'canon_directory': str(self.canon_dir),
            'cache_version': '1.0'
        }
        self._save_to_cache(metadata, self._cache_files['cache_metadata'])
    
    def load_major_cliffhangers(self) -> List[Dict]:
        """Load and cache major cliffhangers"""
        if self._major_cliffhangers is None:
            cache_file = self._cache_files['major_cliffhangers']
            source_file = "5_Major_Cliffhangers_1-100.md"
            
            # Try to load from cache first
            if self._is_cache_valid(cache_file, [source_file]):
                cached_data = self._load_from_cache(cache_file)
                if cached_data is not None:
                    self._major_cliffhangers = cached_data
                    return self._major_cliffhangers
            
            # Parse from source file
            cliffhanger_file = self.canon_dir / source_file
            if cliffhanger_file.exists():
                self._major_cliffhangers = self.cliffhanger_parser.parse_major_cliffhangers(
                    str(cliffhanger_file)
                )
                # Save to cache
                self._save_to_cache(self._major_cliffhangers, cache_file)
                self._update_cache_metadata()
            else:
                self._major_cliffhangers = []
        
        return self._major_cliffhangers
    
    def load_minor_cliffhangers(self) -> List[Dict]:
        """Load and cache minor cliffhangers"""
        if self._minor_cliffhangers is None:
            cache_file = self._cache_files['minor_cliffhangers']
            source_file = "6_Minor_Cliffhangers_1-100.md"
            
            # Try to load from cache first
            if self._is_cache_valid(cache_file, [source_file]):
                cached_data = self._load_from_cache(cache_file)
                if cached_data is not None:
                    self._minor_cliffhangers = cached_data
                    return self._minor_cliffhangers
            
            # Parse from source file
            cliffhanger_file = self.canon_dir / source_file
            if cliffhanger_file.exists():
                self._minor_cliffhangers = self.cliffhanger_parser.parse_minor_cliffhangers(
                    str(cliffhanger_file)
                )
                # Save to cache
                self._save_to_cache(self._minor_cliffhangers, cache_file)
                self._update_cache_metadata()
            else:
                self._minor_cliffhangers = []
        
        return self._minor_cliffhangers
    
    def load_characters(self) -> Dict[str, Dict]:
        """Load and cache character information"""
        if self._characters is None:
            cache_file = self._cache_files['characters']
            source_file = "2_Characters_1-20.md"
            
            # Try to load from cache first
            if self._is_cache_valid(cache_file, [source_file]):
                cached_data = self._load_from_cache(cache_file)
                if cached_data is not None:
                    self._characters = cached_data
                    return self._characters
            
            # Parse from source file
            character_file = self.canon_dir / source_file
            if character_file.exists():
                self._characters = self.character_parser.parse_characters(
                    str(character_file)
                )
                # Save to cache
                self._save_to_cache(self._characters, cache_file)
                self._update_cache_metadata()
            else:
                self._characters = {}
        
        return self._characters
    
    def load_episodes(self) -> List[Dict]:
        """Load and cache all episode summaries"""
        if self._episodes is None:
            cache_file = self._cache_files['episodes']
            source_file = "7_Episodic_Summary_1-100.md"
            
            # Try to load from cache first
            if self._is_cache_valid(cache_file, [source_file]):
                cached_data = self._load_from_cache(cache_file)
                if cached_data is not None:
                    self._episodes = cached_data
                    return self._episodes
            
            # Parse from source file
            summary_file = self.canon_dir / source_file
            if summary_file.exists():
                self._episodes = self.summary_parser.get_all_episodes(
                    str(summary_file)
                )
                # Save to cache
                self._save_to_cache(self._episodes, cache_file)
                self._update_cache_metadata()
            else:
                self._episodes = []
        
        return self._episodes
    
    def get_cliffhanger_by_episode(self, episode_num: int) -> List[Dict]:
        """Get all cliffhangers (major and minor) for a specific episode"""
        major = [c for c in self.load_major_cliffhangers() if c['episode'] == episode_num]
        minor = [c for c in self.load_minor_cliffhangers() if c['episode'] == episode_num]
        return major + minor
    
    def get_episode_summary(self, episode_num: int) -> Optional[Dict]:
        """Get summary for a specific episode"""
        episodes = self.load_episodes()
        for episode in episodes:
            if episode['episode'] == episode_num:
                return episode
        return None
    
    def clear_cache(self):
        """Clear all cached files (force re-parsing on next load)"""
        for cache_file in self._cache_files.values():
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except IOError:
                    pass
        self._major_cliffhangers = None
        self._minor_cliffhangers = None
        self._characters = None
        self._episodes = None
    
    def get_cache_info(self) -> Dict:
        """Get information about cache status"""
        info = {
            'cache_directory': str(self.cache_dir),
            'cache_files': {},
            'cache_metadata': None
        }
        
        # Check cache files
        for key, cache_file in self._cache_files.items():
            if cache_file.exists():
                info['cache_files'][key] = {
                    'exists': True,
                    'size': cache_file.stat().st_size,
                    'modified': datetime.fromtimestamp(cache_file.stat().st_mtime).isoformat()
                }
            else:
                info['cache_files'][key] = {'exists': False}
        
        # Load metadata if available
        if self._cache_files['cache_metadata'].exists():
            info['cache_metadata'] = self._load_from_cache(self._cache_files['cache_metadata'])
        
        return info