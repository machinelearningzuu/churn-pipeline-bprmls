"""
Common PySpark utility functions for data processing and transformation.
"""

import logging
from typing import List, Dict, Optional, Union, Tuple
import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, BooleanType

logger = logging.getLogger(__name__)


def spark_to_pandas(df: DataFrame, max_records: Optional[int] = None) -> pd.DataFrame:
    """
    Convert PySpark DataFrame to pandas DataFrame safely.
    
    Args:
        df: PySpark DataFrame
        max_records: Maximum number of records to convert (for safety)
        
    Returns:
        pandas DataFrame
    """
    try:
        if max_records:
            df = df.limit(max_records)
        
        # Use Arrow optimization if available
        try:
            pandas_df = df.toPandas()
        except:
            # Fallback to regular conversion
            logger.warning("Arrow optimization not available, using standard conversion")
            pandas_df = df.toPandas()
        
        logger.info(f"✓ Converted PySpark DataFrame to pandas: {pandas_df.shape}")
        return pandas_df
        
    except Exception as e:
        logger.error(f"✗ Error converting to pandas: {str(e)}")
        raise


def save_dataframe(
    df: DataFrame,
    path: str,
    format: str = "parquet",
    mode: str = "overwrite",
    **options
) -> None:
    """
    Save PySpark DataFrame in specified format with error handling.
    
    Args:
        df: PySpark DataFrame to save
        path: Output path
        format: Output format (parquet, csv, json)
        mode: Save mode (overwrite, append, ignore, error)
        **options: Additional format-specific options
    """
    try:
        writer = df.write.mode(mode)
        
        if format == "csv":
            # Default CSV options
            csv_options = {
                "header": "true",
                "inferSchema": "true",
                "escape": '"',
                "quote": '"',
                "ignoreLeadingWhiteSpace": "true",
                "ignoreTrailingWhiteSpace": "true"
            }
            csv_options.update(options)
            writer.options(**csv_options).csv(path)
            
        elif format == "parquet":
            # Default Parquet options
            parquet_options = {
                "compression": "snappy"
            }
            parquet_options.update(options)
            writer.options(**parquet_options).parquet(path)
            
        elif format == "json":
            writer.options(**options).json(path)
            
        else:
            writer.options(**options).format(format).save(path)
        
        logger.info(f"✓ Saved DataFrame to {path} as {format}")
        
    except Exception as e:
        logger.error(f"✗ Error saving DataFrame: {str(e)}")
        raise


def load_dataframe(
    spark: SparkSession,
    path: str,
    format: str = "parquet",
    schema: Optional[StructType] = None,
    **options
) -> DataFrame:
    """
    Load DataFrame from specified format with error handling.
    
    Args:
        spark: SparkSession instance
        path: Input path
        format: Input format (parquet, csv, json)
        schema: Optional schema to enforce
        **options: Additional format-specific options
        
    Returns:
        PySpark DataFrame
    """
    try:
        reader = spark.read
        
        if schema:
            reader = reader.schema(schema)
        
        if format == "csv":
            # Default CSV options
            csv_options = {
                "header": "true",
                "inferSchema": "true" if not schema else "false",
                "escape": '"',
                "quote": '"',
                "ignoreLeadingWhiteSpace": "true",
                "ignoreTrailingWhiteSpace": "true"
            }
            csv_options.update(options)
            df = reader.options(**csv_options).csv(path)
            
        elif format == "parquet":
            df = reader.options(**options).parquet(path)
            
        elif format == "json":
            df = reader.options(**options).json(path)
            
        else:
            df = reader.options(**options).format(format).load(path)
        
        logger.info(f"✓ Loaded DataFrame from {path} ({df.count()} rows, {len(df.columns)} columns)")
        return df
        
    except Exception as e:
        logger.error(f"✗ Error loading DataFrame: {str(e)}")
        raise


def get_dataframe_info(df: DataFrame) -> Dict:
    """
    Get comprehensive information about a PySpark DataFrame.
    
    Args:
        df: PySpark DataFrame
        
    Returns:
        Dictionary with DataFrame information
    """
    try:
        info = {
            "columns": df.columns,
            "dtypes": df.dtypes,
            "num_rows": df.count(),
            "num_columns": len(df.columns),
            "schema": df.schema.json(),
            "partitions": df.rdd.getNumPartitions()
        }
        
        # Get column statistics for numeric columns
        numeric_cols = [col for col, dtype in df.dtypes if dtype in ['int', 'bigint', 'float', 'double']]
        if numeric_cols:
            stats = df.select(numeric_cols).describe().collect()
            info["numeric_stats"] = {row[0]: {col: row[i+1] for i, col in enumerate(numeric_cols)} 
                                   for row in stats}
        
        return info
        
    except Exception as e:
        logger.error(f"✗ Error getting DataFrame info: {str(e)}")
        return {}


def check_missing_values(df: DataFrame) -> Dict[str, int]:
    """
    Check for missing values in each column.
    
    Args:
        df: PySpark DataFrame
        
    Returns:
        Dictionary mapping column names to missing value counts
    """
    try:
        missing_counts = {}
        
        for col in df.columns:
            missing_count = df.filter(
                F.col(col).isNull() | 
                F.isnan(col) | 
                (F.col(col) == "")
            ).count()
            missing_counts[col] = missing_count
        
        total_missing = sum(missing_counts.values())
        logger.info(f"✓ Missing value check complete: {total_missing} total missing values")
        
        return missing_counts
        
    except Exception as e:
        logger.error(f"✗ Error checking missing values: {str(e)}")
        return {}


def get_column_stats(df: DataFrame, column: str) -> Dict:
    """
    Get detailed statistics for a specific column.
    
    Args:
        df: PySpark DataFrame
        column: Column name
        
    Returns:
        Dictionary with column statistics
    """
    try:
        col_type = dict(df.dtypes)[column]
        stats = {"column": column, "dtype": col_type}
        
        # Count nulls
        stats["null_count"] = df.filter(F.col(column).isNull()).count()
        stats["null_percentage"] = (stats["null_count"] / df.count()) * 100
        
        if col_type in ['int', 'bigint', 'float', 'double']:
            # Numeric statistics
            numeric_stats = df.select(
                F.mean(column).alias("mean"),
                F.stddev(column).alias("stddev"),
                F.min(column).alias("min"),
                F.max(column).alias("max"),
                F.expr(f"percentile_approx({column}, 0.25)").alias("q1"),
                F.expr(f"percentile_approx({column}, 0.5)").alias("median"),
                F.expr(f"percentile_approx({column}, 0.75)").alias("q3")
            ).collect()[0]
            
            stats.update(numeric_stats.asDict())
            
        else:
            # Categorical statistics
            stats["unique_values"] = df.select(column).distinct().count()
            stats["top_values"] = df.groupBy(column).count() \
                .orderBy(F.desc("count")) \
                .limit(10) \
                .collect()
        
        return stats
        
    except Exception as e:
        logger.error(f"✗ Error getting column stats for {column}: {str(e)}")
        return {}


def cast_columns(
    df: DataFrame,
    column_types: Dict[str, str]
) -> DataFrame:
    """
    Cast columns to specified types.
    
    Args:
        df: PySpark DataFrame
        column_types: Dictionary mapping column names to target types
        
    Returns:
        DataFrame with casted columns
    """
    try:
        for col_name, target_type in column_types.items():
            if col_name in df.columns:
                df = df.withColumn(col_name, F.col(col_name).cast(target_type))
                logger.info(f"✓ Cast {col_name} to {target_type}")
            else:
                logger.warning(f"⚠ Column {col_name} not found in DataFrame")
        
        return df
        
    except Exception as e:
        logger.error(f"✗ Error casting columns: {str(e)}")
        raise


def optimize_dataframe(df: DataFrame) -> DataFrame:
    """
    Optimize DataFrame for better performance.
    
    Args:
        df: PySpark DataFrame
        
    Returns:
        Optimized DataFrame
    """
    try:
        # Get current partition count
        current_partitions = df.rdd.getNumPartitions()
        
        # Estimate optimal partitions (rough heuristic)
        row_count = df.count()
        optimal_partitions = max(1, min(200, row_count // 10000))
        
        if current_partitions > optimal_partitions * 2:
            # Too many partitions, coalesce
            df = df.coalesce(optimal_partitions)
            logger.info(f"✓ Coalesced from {current_partitions} to {optimal_partitions} partitions")
        elif current_partitions < optimal_partitions // 2:
            # Too few partitions, repartition
            df = df.repartition(optimal_partitions)
            logger.info(f"✓ Repartitioned from {current_partitions} to {optimal_partitions} partitions")
        
        # Cache if DataFrame will be reused
        df.cache()
        logger.info("✓ DataFrame cached for reuse")
        
        return df
        
    except Exception as e:
        logger.error(f"✗ Error optimizing DataFrame: {str(e)}")
        return df


def sample_dataframe(
    df: DataFrame,
    n: Optional[int] = None,
    fraction: Optional[float] = None,
    seed: int = 42
) -> DataFrame:
    """
    Sample rows from DataFrame.
    
    Args:
        df: PySpark DataFrame
        n: Number of rows to sample
        fraction: Fraction of rows to sample (0-1)
        seed: Random seed
        
    Returns:
        Sampled DataFrame
    """
    try:
        if n is not None:
            # Sample specific number of rows
            total_rows = df.count()
            sample_fraction = min(1.0, n / total_rows * 1.1)  # Slight oversampling
            sampled = df.sample(withReplacement=False, fraction=sample_fraction, seed=seed)
            sampled = sampled.limit(n)
            
        elif fraction is not None:
            # Sample fraction of rows
            sampled = df.sample(withReplacement=False, fraction=fraction, seed=seed)
            
        else:
            raise ValueError("Either 'n' or 'fraction' must be specified")
        
        logger.info(f"✓ Sampled {sampled.count()} rows from {df.count()} total rows")
        return sampled
        
    except Exception as e:
        logger.error(f"✗ Error sampling DataFrame: {str(e)}")
        raise


def create_ml_features(
    df: DataFrame,
    feature_cols: List[str],
    label_col: str,
    features_col: str = "features"
) -> DataFrame:
    """
    Create feature vector for ML algorithms.
    
    Args:
        df: PySpark DataFrame
        feature_cols: List of feature column names
        label_col: Label column name
        features_col: Name for the output features column
        
    Returns:
        DataFrame with features vector
    """
    try:
        from pyspark.ml.feature import VectorAssembler
        
        # Create vector assembler
        assembler = VectorAssembler(
            inputCols=feature_cols,
            outputCol=features_col,
            handleInvalid="skip"
        )
        
        # Transform data
        df_ml = assembler.transform(df)
        
        # Select only necessary columns
        df_ml = df_ml.select(features_col, label_col)
        
        logger.info(f"✓ Created ML features from {len(feature_cols)} columns")
        return df_ml
        
    except Exception as e:
        logger.error(f"✗ Error creating ML features: {str(e)}")
        raise
