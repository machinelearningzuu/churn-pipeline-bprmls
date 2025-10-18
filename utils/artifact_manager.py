"""
Artifact management utilities for timestamp-based versioning
"""

import os
import glob
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ArtifactManager:
    """Manages timestamped artifacts for ML pipeline"""
    
    def __init__(self, base_dir: str = "data/artifacts"):
        self.base_dir = Path(base_dir)
        self.timestamp_format = "%Y%m%d%H%M%S"
        
    def generate_timestamp(self) -> str:
        """Generate timestamp string for artifact naming"""
        return datetime.now().strftime(self.timestamp_format)
    
    def create_timestamped_paths(self, base_names: List[str], timestamp: Optional[str] = None, 
                                subdir: Optional[str] = None, format_ext: str = "csv") -> Dict[str, str]:
        """
        Create timestamped paths for artifacts using timestamp folders
        
        Args:
            base_names: List of base names (e.g., ['X_train', 'X_test', 'Y_train', 'Y_test'])
            timestamp: Optional timestamp string, generates new if None
            subdir: Optional subdirectory, defaults to format_ext folder
            format_ext: File extension (csv, parquet, etc.)
        
        Returns:
            Dictionary mapping base names to timestamped paths
        """
        if timestamp is None:
            timestamp = self.generate_timestamp()
            
        # Use format-specific subdirectory if subdir not specified
        if subdir is None:
            subdir = format_ext
            
        paths = {}
        # Create timestamp-based folder structure: data/artifacts/csv/20251004195220/
        timestamp_dir = self.base_dir / subdir / timestamp
        timestamp_dir.mkdir(parents=True, exist_ok=True)
        
        for base_name in base_names:
            filename = f"{base_name}.{format_ext}"
            full_path = timestamp_dir / filename
            paths[base_name] = str(full_path)
                
        return paths
    
    def get_latest_artifacts(self, base_names: List[str], subdir: Optional[str] = None, 
                           format_ext: str = "csv") -> Dict[str, str]:
        """
        Get paths to the latest timestamped artifacts
        
        Args:
            base_names: List of base names to find
            subdir: Optional subdirectory, defaults to format_ext folder
            format_ext: File extension
            
        Returns:
            Dictionary mapping base names to latest artifact paths
        """
        # Use format-specific subdirectory if subdir not specified
        if subdir is None:
            subdir = format_ext
            
        latest_paths = {}
        
        # Find all timestamp directories
        format_dir = self.base_dir / subdir
        if not format_dir.exists():
            logger.warning(f"Format directory does not exist: {format_dir}")
            return {}
            
        # Get all timestamp directories (14-digit folders)
        timestamp_dirs = []
        for item in format_dir.iterdir():
            if item.is_dir() and re.match(r'^\d{14}$', item.name):
                try:
                    timestamp = datetime.strptime(item.name, self.timestamp_format)
                    timestamp_dirs.append((timestamp, item))
                except ValueError:
                    continue
        
        if not timestamp_dirs:
            logger.warning(f"No timestamp directories found in {format_dir}")
            # Fallback to old artifact structure (artifacts/data/)
            for base_name in base_names:
                old_fallback_path = f"artifacts/data/{base_name}.{format_ext}"
                if os.path.exists(old_fallback_path):
                    latest_paths[base_name] = old_fallback_path
                    logger.info(f"Using legacy fallback path for {base_name}: {old_fallback_path}")
            return latest_paths
        
        # Get the latest timestamp directory
        latest_timestamp, latest_dir = max(timestamp_dirs, key=lambda x: x[0])
        logger.info(f"Using latest timestamp directory: {latest_dir}")
        
        # Build paths for each base name in the latest directory
        for base_name in base_names:
            artifact_path = latest_dir / f"{base_name}.{format_ext}"
            if artifact_path.exists():
                latest_paths[base_name] = str(artifact_path)
                logger.info(f"Latest artifact for {base_name}: {artifact_path}")
            else:
                logger.warning(f"Artifact not found: {artifact_path}")
        
        return latest_paths
    
    def get_artifact_info(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Get information about all available artifacts
        
        Returns:
            Dictionary mapping base names to list of (timestamp, filepath) tuples
        """
        artifact_info = {}
        
        for ext in ["csv", "parquet"]:
            format_dir = self.base_dir / ext
            if not format_dir.exists():
                continue
                
            # Find all timestamp directories
            for timestamp_item in format_dir.iterdir():
                if timestamp_item.is_dir() and re.match(r'^\d{14}$', timestamp_item.name):
                    timestamp_str = timestamp_item.name
                    
                    # Find all artifacts in this timestamp directory
                    for artifact_file in timestamp_item.iterdir():
                        if artifact_file.suffix == f'.{ext}':
                            base_name = artifact_file.stem  # filename without extension
                            
                            if base_name not in artifact_info:
                                artifact_info[base_name] = []
                            
                            artifact_info[base_name].append((timestamp_str, str(artifact_file)))
        
        # Sort each list by timestamp (newest first)
        for base_name in artifact_info:
            artifact_info[base_name].sort(key=lambda x: x[0], reverse=True)
        
        return artifact_info
    
    def cleanup_old_artifacts(self, base_names: List[str], keep_count: int = 5, 
                            subdir: Optional[str] = None, format_ext: str = "csv"):
        """
        Clean up old artifacts, keeping only the most recent ones
        
        Args:
            base_names: List of base names to clean up (not used in folder-based approach)
            keep_count: Number of recent timestamp directories to keep
            subdir: Optional subdirectory, defaults to format_ext folder
            format_ext: File extension
        """
        # Use format-specific subdirectory if subdir not specified
        if subdir is None:
            subdir = format_ext
            
        format_dir = self.base_dir / subdir
        if not format_dir.exists():
            return
            
        # Get all timestamp directories
        timestamp_dirs = []
        for item in format_dir.iterdir():
            if item.is_dir() and re.match(r'^\d{14}$', item.name):
                try:
                    timestamp = datetime.strptime(item.name, self.timestamp_format)
                    timestamp_dirs.append((timestamp, item))
                except ValueError:
                    continue
        
        if len(timestamp_dirs) <= keep_count:
            return
        
        # Sort by timestamp (newest first) and remove old directories
        timestamp_dirs.sort(key=lambda x: x[0], reverse=True)
        dirs_to_remove = timestamp_dirs[keep_count:]
        
        for _, dir_path in dirs_to_remove:
            try:
                import shutil
                shutil.rmtree(dir_path)
                logger.info(f"Removed old timestamp directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to remove {dir_path}: {e}")


def get_timestamped_artifact_paths(timestamp: Optional[str] = None, format_ext: str = "csv") -> Dict[str, str]:
    """
    Convenience function to get timestamped paths for standard ML artifacts
    
    Args:
        timestamp: Optional timestamp, generates new if None
        format_ext: File extension (csv, parquet)
        
    Returns:
        Dictionary with timestamped paths for X_train, X_test, Y_train, Y_test
    """
    manager = ArtifactManager()
    base_names = ['X_train', 'X_test', 'Y_train', 'Y_test']
    return manager.create_timestamped_paths(base_names, timestamp, format_ext=format_ext)


def get_latest_artifact_paths(format_ext: str = "csv") -> Dict[str, str]:
    """
    Convenience function to get latest artifact paths
    
    Args:
        format_ext: File extension (csv, parquet)
        
    Returns:
        Dictionary with latest paths for X_train, X_test, Y_train, Y_test
    """
    manager = ArtifactManager()
    base_names = ['X_train', 'X_test', 'Y_train', 'Y_test']
    return manager.get_latest_artifacts(base_names, format_ext=format_ext)
