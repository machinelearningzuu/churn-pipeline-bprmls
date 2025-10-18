"""
Setup script for ML Pipeline Project
"""
from setuptools import setup, find_packages

setup(
    name="ml-pipeline-project",
    version="1.0.0",
    description="Production-Ready Machine Learning Pipeline System",
    author="ML Engineering Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.1.0",
        "scipy>=1.9.0",
        "pyspark>=3.4.0",
        "xgboost>=2.1.0",
        "lightgbm>=3.3.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "plotly>=5.10.0",
        "pyyaml>=6.0",
        "python-dotenv>=0.19.0",
        "openpyxl>=3.0.0",
        "xlrd>=2.0.0",
        "fastapi>=0.95.0",
        "uvicorn>=0.20.0",
        "pydantic>=2.0.0,<2.11.2",
        "mlflow>=1.30.0",
        "wandb>=0.15.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "jupyter>=1.0.0",
        "ipykernel>=6.0.0",
        "black>=22.0.0",
        "flake8>=5.0.0",
        "groq>=0.11.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
        "airflow": [
            "apache-airflow>=2.7.0,<2.8.0",
            "apache-airflow-providers-apache-spark>=3.0.0",
        ],
        "kafka": [
            "confluent-kafka>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ml-pipeline=pipelines.data_pipeline:main",
            "ml-train=pipelines.training_pipeline:main",
            "ml-inference=pipelines.inference_pipeline:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
