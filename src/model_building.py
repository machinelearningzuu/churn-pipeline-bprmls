import joblib, os
from typing import Dict, Any
from datetime import datetime
from xgboost import XGBClassifier
from abc import ABC, abstractmethod
from sklearn.ensemble import RandomForestClassifier

# PySpark MLlib imports
# Manual PySpark availability flag - set to False to prioritize scikit-learn
PYSPARK_AVAILABLE = False  # Set to True to enable PySpark, False for sklearn-only

# Conditional PySpark imports
if PYSPARK_AVAILABLE:
    try:
        from pyspark.ml.classification import RandomForestClassifier as SparkRandomForestClassifier
        from pyspark.ml.classification import GBTClassifier as SparkGBTClassifier
        from pyspark.ml.classification import LogisticRegression as SparkLogisticRegression
        from pyspark.ml.feature import VectorAssembler
        from pyspark.ml import Pipeline
    except ImportError:
        PYSPARK_AVAILABLE = False
else:
    SparkRandomForestClassifier = None
    SparkGBTClassifier = None
    SparkLogisticRegression = None

class BaseModelBuilder(ABC):
    def __init__(
                self,
                model_name:str,
                **kwargs
                ):
        self.model_name = model_name
        self.model = None 
        self.model_params = kwargs
    
    @abstractmethod
    def build_model(self):
        pass 

    def save_model(self, filepath):
        if self.model is None:
            raise ValueError("No model to save. Build the model first.")
        
        joblib.dump(self.model, filepath)
        
    def load_model(self, filepath):
        if not os.path.exists(filepath):
            raise ValueError("Can't load. File not found.")
        
        self.model = joblib.load(filepath)

class RandomForestModelBuilder(BaseModelBuilder):
    def __init__(self, **kwargs):
        default_params = {
                        'max_depth': 10,
                        'n_estimators': 100, 
                        'min_samples_split': 2, 
                        'min_samples_leaf': 1, 
                        'random_state': 42
                        }
        default_params.update(kwargs)
        super().__init__('RandomForest', **default_params)

    def build_model(self):
        self.model = RandomForestClassifier(**self.model_params)
        return self.model
    
class XGboostModelBuilder(BaseModelBuilder):
    def __init__(self, **kwargs):
        default_params = {
                        'max_depth': 10,
                        'n_estimators': 100, 
                        'random_state': 42
                        }
        default_params.update(kwargs)
        super().__init__('XGboost', **default_params)

    def build_model(self):
        self.model = XGBClassifier(**self.model_params)
        return self.model


class SparkRandomForestModelBuilder(BaseModelBuilder):
    def __init__(self, **kwargs):
        default_params = {
            'maxDepth': 10,
            'numTrees': 100,
            'seed': 42
        }
        default_params.update(kwargs)
        super().__init__('SparkRandomForest', **default_params)

    def build_model(self):
        self.model = SparkRandomForestClassifier(**self.model_params)
        return self.model

    def save_model(self, filepath):
        if self.model is None:
            raise ValueError("No model to save. Build the model first.")
        
        # For PySpark models, we need to save the fitted pipeline
        self.model.write().overwrite().save(filepath)
        
    def load_model(self, filepath):
        if not os.path.exists(filepath):
            raise ValueError("Can't load. File not found.")
        
        from pyspark.ml.classification import RandomForestClassificationModel
        self.model = RandomForestClassificationModel.load(filepath)


class SparkGBTModelBuilder(BaseModelBuilder):
    def __init__(self, **kwargs):
        default_params = {
            'maxDepth': 5,
            'maxIter': 100,
            'seed': 42
        }
        default_params.update(kwargs)
        super().__init__('SparkGBT', **default_params)

    def build_model(self):
        self.model = SparkGBTClassifier(**self.model_params)
        return self.model

    def save_model(self, filepath):
        if self.model is None:
            raise ValueError("No model to save. Build the model first.")
        
        self.model.write().overwrite().save(filepath)
        
    def load_model(self, filepath):
        if not os.path.exists(filepath):
            raise ValueError("Can't load. File not found.")
        
        from pyspark.ml.classification import GBTClassificationModel
        self.model = GBTClassificationModel.load(filepath)