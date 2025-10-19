# Scripts Directory

This directory contains all utility scripts for the ML pipeline project.

## Shell Scripts (.sh)

### Pipeline Utilities
- **`run_local.sh`** - Wrapper script for running Python pipelines locally
  - Usage: `./scripts/run_local.sh python pipelines/data_pipeline.py`
  - Handles virtual environment activation and Python path setup

### AWS RDS Management
- **`setup_rds.sh`** - Connect to existing RDS instance
  - **Connects to existing RDS** (does NOT create new instances)
  - Auto-configures security groups (adds your IP)
  - Creates MLflow and Airflow databases
  - Generates .env configuration
  - **Prerequisites**: RDS instance must already exist in AWS
  - Usage:
    ```bash
    # With credentials in .env
    ./scripts/setup_rds.sh
    
    # Or with environment variables
    RDS_IDENTIFIER=my-db RDS_PASSWORD=mypass ./scripts/setup_rds.sh
    ```

- **`test_rds_connection.sh`** - Test RDS connectivity
  - Verifies database connections
  - Creates databases if needed
  - Validates configuration

### Docker Optimization
- **`migrate_to_optimized_docker.sh`** - Docker migration helper
  - Migrates to optimized Docker setup
  - Updates configurations

## Python Scripts (.py)

### Data Management
- **`upload_data_to_s3.py`** - Upload datasets to S3
  - Uploads raw and processed data
  - Handles S3 bucket configuration

### Database Visualization
- **`visualize_rds.py`** - RDS database visualization tool
  - Shows database schemas and table information
  - Displays row counts, column details, and sizes
  - Usage: `python scripts/visualize_rds.py [--database DB_NAME] [--columns]`

## Usage from Makefile

All scripts are referenced in the Makefile with the `scripts/` prefix:

```makefile
# Examples
make data-pipeline          # Uses scripts/run_local.sh
make rds-show-all          # Uses scripts/visualize_rds.py
./scripts/setup_rds.sh     # Direct execution
```

## Permissions

All shell scripts should be executable:
```bash
chmod +x scripts/*.sh
```

## Directory Structure Benefits

✅ **Organized**: All utility scripts in one place  
✅ **Clean Root**: No clutter in project root  
✅ **Discoverable**: Easy to find and understand  
✅ **Maintainable**: Grouped by functionality  
✅ **Professional**: Follows best practices  

