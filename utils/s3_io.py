"""
S3 I/O utilities for ML pipeline using boto3
"""

import boto3
import botocore.config
import pandas as pd
import pickle
import io
import logging
from typing import Any, Optional, List
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(__file__))
from config import get_s3_bucket, get_aws_region, get_s3_kms_arn

logger = logging.getLogger(__name__)


def get_s3_client():
    """Create configured S3 client with retries and timeouts, Docker and local compatible"""
    import botocore.client
    import botocore.config
    
    # Get credentials and region
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region = get_aws_region()
    
    # If environment variables are not set, try to read from Docker mounted credentials file
    if not aws_access_key_id or not aws_secret_access_key:
        credentials_file = '/aws/credentials'  # Docker mount path
        if os.path.exists(credentials_file):
            try:
                # Read AWS credentials from mounted file (Docker environment)
                with open(credentials_file, 'r') as f:
                    content = f.read()
                    
                # Parse the credentials file
                import re
                access_key_match = re.search(r'aws_access_key_id\s*=\s*(.+)', content)
                secret_key_match = re.search(r'aws_secret_access_key\s*=\s*(.+)', content)
                
                if access_key_match and secret_key_match:
                    aws_access_key_id = access_key_match.group(1).strip()
                    aws_secret_access_key = secret_key_match.group(1).strip()
                    logger.info("✅ AWS credentials loaded from Docker mounted file")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to read AWS credentials from {credentials_file}: {e}")
    
    # Always use explicit credentials if available to avoid profile issues
    if aws_access_key_id and aws_secret_access_key:
        logger.info("Using explicit AWS credentials")
        
        # Aggressively clear all AWS config environment variables to avoid profile conflicts
        config_vars_to_clear = [
            'AWS_CONFIG_FILE', 'AWS_SHARED_CREDENTIALS_FILE', 'AWS_PROFILE',
            'AWS_DEFAULT_PROFILE', 'AWS_CA_BUNDLE', 'AWS_METADATA_SERVICE_TIMEOUT',
            'AWS_METADATA_SERVICE_NUM_ATTEMPTS', 'AWS_STS_REGIONAL_ENDPOINTS'
        ]
        
        original_values = {}
        for var in config_vars_to_clear:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
        
        try:
            # Create client with completely clean environment
            import boto3
            config = botocore.config.Config(
                retries={"max_attempts": 5, "mode": "standard"},
                connect_timeout=5,
                read_timeout=30
            )
            
            client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                config=config
            )
            return client
            
        finally:
            # Restore original environment variables
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
    
    # Final fallback: try default boto3 behavior (should rarely be reached)
    logger.warning("⚠️ No explicit credentials found, trying default AWS credential chain")
    import boto3
    config = botocore.config.Config(
        retries={"max_attempts": 5, "mode": "standard"},
        connect_timeout=5,
        read_timeout=30
    )
    return boto3.client('s3', region_name=region, config=config)


def put_bytes(data: bytes, *, key: str, content_type: Optional[str] = None) -> None:
    """
    Upload bytes data to S3 with KMS encryption
    
    Args:
        data: Bytes data to upload
        key: S3 key (path)
        content_type: MIME content type
    """
    bucket = get_s3_bucket()
    kms_key = get_s3_kms_arn()
    s3_client = get_s3_client()
    
    put_kwargs = {
        'Bucket': bucket,
        'Key': key,
        'Body': data,
    }
    
    if content_type:
        put_kwargs['ContentType'] = content_type
    
    if kms_key:
        put_kwargs.update({
            'ServerSideEncryption': 'aws:kms',
            'SSEKMSKeyId': kms_key
        })
    
    try:
        s3_client.put_object(**put_kwargs)
        logger.info(f"✅ Uploaded {len(data)} bytes to s3://{bucket}/{key}")
    except Exception as e:
        logger.error(f"❌ Failed to upload to s3://{bucket}/{key}: {e}")
        raise


def get_bytes(key: str) -> bytes:
    """
    Download bytes data from S3
    
    Args:
        key: S3 key (path)
        
    Returns:
        Bytes data
    """
    bucket = get_s3_bucket()
    s3_client = get_s3_client()
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        data = response['Body'].read()
        logger.info(f"✅ Downloaded {len(data)} bytes from s3://{bucket}/{key}")
        return data
    except Exception as e:
        logger.error(f"❌ Failed to download from s3://{bucket}/{key}: {e}")
        raise


def upload_file(local_path, *, key: str) -> None:
    """
    Upload file to S3 with multipart transfer and KMS encryption
    
    Args:
        local_path: Local file path
        key: S3 key (path)
    """
    bucket = get_s3_bucket()
    kms_key = get_s3_kms_arn()
    s3_client = get_s3_client()
    
    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")
    
    extra_args = {}
    if kms_key:
        extra_args.update({
            'ServerSideEncryption': 'aws:kms',
            'SSEKMSKeyId': kms_key
        })
    
    try:
        s3_client.upload_file(
            str(local_path), 
            bucket, 
            key, 
            ExtraArgs=extra_args
        )
        file_size = local_path.stat().st_size
        logger.info(f"✅ Uploaded {file_size} bytes from {local_path} to s3://{bucket}/{key}")
    except Exception as e:
        logger.error(f"❌ Failed to upload {local_path} to s3://{bucket}/{key}: {e}")
        raise


def download_file(key: str, *, local_path) -> None:
    """
    Download file from S3 to local path (for debugging only)
    
    Args:
        key: S3 key (path)
        local_path: Local file path to save
    """
    bucket = get_s3_bucket()
    s3_client = get_s3_client()
    
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        s3_client.download_file(bucket, key, str(local_path))
        file_size = local_path.stat().st_size
        logger.info(f"✅ Downloaded {file_size} bytes from s3://{bucket}/{key} to {local_path}")
    except Exception as e:
        logger.error(f"❌ Failed to download s3://{bucket}/{key} to {local_path}: {e}")
        raise


def write_df_csv(df: pd.DataFrame, *, key: str) -> None:
    """
    Write pandas DataFrame to S3 as CSV
    
    Args:
        df: DataFrame to write
        key: S3 key (path)
    """
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    csv_data = buffer.getvalue().encode('utf-8')
    
    put_bytes(csv_data, key=key, content_type='text/csv')
    logger.info(f"✅ Wrote DataFrame ({df.shape}) as CSV to s3://{get_s3_bucket()}/{key}")


def read_df_csv(*, key: str) -> pd.DataFrame:
    """
    Read pandas DataFrame from S3 CSV
    
    Args:
        key: S3 key (path)
        
    Returns:
        pandas DataFrame
    """
    csv_data = get_bytes(key)
    buffer = io.StringIO(csv_data.decode('utf-8'))
    df = pd.read_csv(buffer)
    
    logger.info(f"✅ Read DataFrame ({df.shape}) from CSV s3://{get_s3_bucket()}/{key}")
    return df


def write_df_json(df: pd.DataFrame, *, key: str) -> None:
    """
    Write pandas DataFrame to S3 as JSON
    
    Args:
        df: DataFrame to write
        key: S3 key (path)
    """
    json_data = df.to_json(orient='records').encode('utf-8')
    put_bytes(json_data, key=key, content_type='application/json')
    logger.info(f"✅ Wrote DataFrame ({df.shape}) as JSON to s3://{get_s3_bucket()}/{key}")


def read_df_json(*, key: str) -> pd.DataFrame:
    """
    Read pandas DataFrame from S3 JSON
    
    Args:
        key: S3 key (path)
        
    Returns:
        pandas DataFrame
    """
    json_data = get_bytes(key)
    df = pd.read_json(io.StringIO(json_data.decode('utf-8')), orient='records')
    
    logger.info(f"✅ Read DataFrame ({df.shape}) from JSON s3://{get_s3_bucket()}/{key}")
    return df


def write_pickle(obj: Any, *, key: str) -> None:
    """
    Write Python object to S3 using pickle
    
    Args:
        obj: Object to serialize
        key: S3 key (path)
    """
    buffer = io.BytesIO()
    pickle.dump(obj, buffer)
    pickle_data = buffer.getvalue()
    
    put_bytes(pickle_data, key=key, content_type='application/octet-stream')
    logger.info(f"✅ Wrote pickled object ({len(pickle_data)} bytes) to s3://{get_s3_bucket()}/{key}")


def read_pickle(*, key: str) -> Any:
    """
    Read Python object from S3 pickle
    
    Args:
        key: S3 key (path)
        
    Returns:
        Unpickled object
    """
    pickle_data = get_bytes(key)
    buffer = io.BytesIO(pickle_data)
    obj = pickle.load(buffer)
    
    logger.info(f"✅ Read pickled object ({len(pickle_data)} bytes) from s3://{get_s3_bucket()}/{key}")
    return obj


def list_keys(prefix: str = "") -> List[str]:
    """
    List S3 keys with given prefix using pagination
    
    Args:
        prefix: Key prefix to filter
        
    Returns:
        List of S3 keys
    """
    bucket = get_s3_bucket()
    s3_client = get_s3_client()
    
    keys = []
    paginator = s3_client.get_paginator('list_objects_v2')
    
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' in page:
                keys.extend([obj['Key'] for obj in page['Contents']])
        
        logger.info(f"✅ Listed {len(keys)} keys with prefix '{prefix}' from s3://{bucket}")
        return keys
    except Exception as e:
        logger.error(f"❌ Failed to list keys with prefix '{prefix}' from s3://{bucket}: {e}")
        raise


def delete_key(key: str) -> None:
    """
    Delete S3 key
    
    Args:
        key: S3 key (path) to delete
    """
    bucket = get_s3_bucket()
    s3_client = get_s3_client()
    
    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        logger.info(f"✅ Deleted s3://{bucket}/{key}")
    except Exception as e:
        logger.error(f"❌ Failed to delete s3://{bucket}/{key}: {e}")
        raise


def key_exists(key: str) -> bool:
    """
    Check if S3 key exists
    
    Args:
        key: S3 key (path) to check
        
    Returns:
        True if key exists, False otherwise
    """
    bucket = get_s3_bucket()
    s3_client = get_s3_client()
    
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except s3_client.exceptions.NoSuchKey:
        return False
    except Exception as e:
        logger.error(f"❌ Error checking existence of s3://{bucket}/{key}: {e}")
        return False
