"""
S3-based artifact management utilities for ML pipeline
"""

import re
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import logging

import sys
import os
sys.path.append(os.path.dirname(__file__))
from s3_io import list_keys
from config import get_s3_bucket

logger = logging.getLogger(__name__)


class S3ArtifactManager:
    """Manages timestamped artifacts in S3 for ML pipeline"""
    
    def __init__(self, base_prefix: str = "artifacts"):
        self.base_prefix = base_prefix.rstrip('/')
        self.timestamp_format = "%Y%m%d%H%M%S"
        self.bucket = get_s3_bucket()
        
    def generate_timestamp(self) -> str:
        """Generate timestamp string for artifact naming"""
        return datetime.now().strftime(self.timestamp_format)
    
    def create_s3_paths(self, base_names: List[str], timestamp: Optional[str] = None, 
                       artifact_type: str = "data_artifacts", format_ext: str = "csv") -> Dict[str, str]:
        """
        Create S3 key paths for artifacts using proper folder structure
        
        Args:
            base_names: List of base names (e.g., ['X_train', 'X_test', 'Y_train', 'Y_test'])
            timestamp: Optional timestamp string, generates new if None
            artifact_type: Type of artifact (data_artifacts, train_artifacts, inference_artifacts)
            format_ext: File extension (csv, pkl, json, etc.)
        
        Returns:
            Dictionary mapping base names to S3 key paths
        """
        if timestamp is None:
            timestamp = self.generate_timestamp()
            
        paths = {}
        # Create S3 key structure: artifacts/data_artifacts/20251004201117/X_train.csv
        for base_name in base_names:
            filename = f"{base_name}.{format_ext}"
            s3_key = f"{self.base_prefix}/{artifact_type}/{timestamp}/{filename}"
            paths[base_name] = s3_key
                
        logger.info(f"📁 Created S3 paths with timestamp: {timestamp}")
        for name, path in paths.items():
            logger.info(f"   {name}: s3://{self.bucket}/{path}")
            
        return paths
    
    def get_latest_artifacts(self, base_names: List[str], artifact_type: str = "data_artifacts", 
                           format_ext: str = "csv") -> Dict[str, str]:
        """
        Get S3 key paths to the latest timestamped artifacts
        
        Args:
            base_names: List of base names to find
            artifact_type: Type of artifact (data_artifacts, train_artifacts, inference_artifacts)
            format_ext: File extension
            
        Returns:
            Dictionary mapping base names to latest S3 key paths
        """
        latest_paths = {}
        
        # List all keys under the specific artifact type directory
        prefix = f"{self.base_prefix}/{artifact_type}/"
        try:
            all_keys = list_keys(prefix=prefix)
        except Exception as e:
            logger.error(f"Failed to list S3 keys with prefix {prefix}: {e}")
            return {}
        
        # Extract timestamp directories from keys
        timestamp_dirs = set()
        for key in all_keys:
            # Extract timestamp from key like "artifacts/data_artifacts/20251004201117/X_train.csv"
            relative_key = key[len(prefix):]  # Remove "artifacts/data_artifacts/" prefix
            if '/' in relative_key:
                timestamp_part = relative_key.split('/')[0]
                if re.match(r'^\d{14}$', timestamp_part):
                    timestamp_dirs.add(timestamp_part)
        
        if not timestamp_dirs:
            logger.warning(f"No timestamp directories found in s3://{self.bucket}/{prefix}")
            return {}
        
        # Get the latest timestamp
        latest_timestamp = max(timestamp_dirs)
        logger.info(f"Using latest timestamp directory: {self.base_prefix}/{artifact_type}/{latest_timestamp}")
        
        # Build paths for each base name in the latest timestamp
        for base_name in base_names:
            s3_key = f"{self.base_prefix}/{artifact_type}/{latest_timestamp}/{base_name}.{format_ext}"
            # Check if the key exists by looking in our list
            if any(key == s3_key for key in all_keys):
                latest_paths[base_name] = s3_key
                logger.info(f"Latest artifact for {base_name}: s3://{self.bucket}/{s3_key}")
            else:
                logger.warning(f"Artifact not found: s3://{self.bucket}/{s3_key}")
        
        return latest_paths
    
    def get_artifact_info(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Get information about all available artifacts in S3
        
        Returns:
            Dictionary mapping base names to list of (timestamp, s3_key) tuples
        """
        artifact_info = {}
        
        for ext in ["csv", "parquet"]:
            prefix = f"{self.base_prefix}/{ext}/"
            try:
                all_keys = list_keys(prefix=prefix)
            except Exception as e:
                logger.error(f"Failed to list keys for {ext}: {e}")
                continue
                
            # Parse keys to extract base names and timestamps
            for key in all_keys:
                relative_key = key[len(prefix):]  # Remove prefix
                if '/' in relative_key:
                    parts = relative_key.split('/')
                    if len(parts) >= 2:
                        timestamp_str = parts[0]
                        filename = parts[1]
                        
                        if re.match(r'^\d{14}$', timestamp_str) and filename.endswith(f'.{ext}'):
                            base_name = filename[:-len(f'.{ext}')]  # Remove extension
                            
                            if base_name not in artifact_info:
                                artifact_info[base_name] = []
                            
                            artifact_info[base_name].append((timestamp_str, key))
        
        # Sort each list by timestamp (newest first)
        for base_name in artifact_info:
            artifact_info[base_name].sort(key=lambda x: x[0], reverse=True)
        
        return artifact_info
    
    def cleanup_old_artifacts(self, artifact_type: str = "data_artifacts", keep_count: int = 10) -> None:
        """
        Clean up old timestamp directories in S3, keeping only the most recent ones
        
        Args:
            artifact_type: Type of artifact (data_artifacts, train_artifacts, inference_artifacts)
            keep_count: Number of recent timestamp directories to keep
        """
        prefix = f"{self.base_prefix}/{artifact_type}/"
        
        try:
            all_keys = list_keys(prefix=prefix)
        except Exception as e:
            logger.error(f"Failed to list keys for cleanup: {e}")
            return
        
        # Extract unique timestamp directories
        timestamp_dirs = set()
        for key in all_keys:
            relative_key = key[len(prefix):]
            if '/' in relative_key:
                timestamp_part = relative_key.split('/')[0]
                if re.match(r'^\d{14}$', timestamp_part):
                    timestamp_dirs.add(timestamp_part)
        
        if len(timestamp_dirs) <= keep_count:
            logger.info(f"Only {len(timestamp_dirs)} timestamp directories found, no cleanup needed")
            return
        
        # Sort timestamps and identify old ones to remove
        sorted_timestamps = sorted(timestamp_dirs, reverse=True)  # Newest first
        old_timestamps = sorted_timestamps[keep_count:]
        
        # Delete all keys in old timestamp directories
        from s3_io import delete_key
        
        for old_timestamp in old_timestamps:
            old_prefix = f"{prefix}{old_timestamp}/"
            keys_to_delete = [key for key in all_keys if key.startswith(old_prefix)]
            
            for key in keys_to_delete:
                try:
                    delete_key(key)
                except Exception as e:
                    logger.error(f"Failed to delete {key}: {e}")
            
            if keys_to_delete:
                logger.info(f"🗑️ Removed {len(keys_to_delete)} artifacts from timestamp {old_timestamp}")


def get_s3_artifact_paths(timestamp: Optional[str] = None, format_ext: str = "csv") -> Dict[str, str]:
    """
    Convenience function to get S3 paths for standard ML artifacts
    
    Args:
        timestamp: Optional timestamp, generates new if None
        format_ext: File extension (csv, parquet)
        
    Returns:
        Dictionary with S3 key paths for X_train, X_test, Y_train, Y_test
    """
    manager = S3ArtifactManager()
    base_names = ['X_train', 'X_test', 'Y_train', 'Y_test']
    return manager.create_s3_paths(base_names, timestamp, format_ext=format_ext)


def get_latest_s3_artifacts(format_ext: str = "csv") -> Dict[str, str]:
    """
    Convenience function to get latest S3 artifact paths
    
    Args:
        format_ext: File extension (csv, parquet)
        
    Returns:
        Dictionary with latest S3 key paths for X_train, X_test, Y_train, Y_test
    """
    manager = S3ArtifactManager()
    base_names = ['X_train', 'X_test', 'Y_train', 'Y_test']
    return manager.get_latest_artifacts(base_names, format_ext=format_ext)
