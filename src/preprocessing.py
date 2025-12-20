from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd

def build_preprocessing_pipeline(feature_names):
    pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    return pipeline

def split_features_target(df, target):
    X = df.drop(columns=[target])
    y = df[target]

    X = X.select_dtypes(include=[np.number])

    return X, y
