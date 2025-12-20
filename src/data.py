import pandas as pd
from pathlib import Path

TARGET = "SeriousDlqin2yrs"

def load_data(file_path: str = "data/cs-training.csv") -> pd.DataFrame:
    """Load and do basic inspection of credit data."""
    
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load data
    df = pd.read_csv(file_path)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    # Validate target
    if TARGET not in df.columns:
        raise ValueError(f"Target column '{TARGET}' missing")

    # Basic info (learning/debugging stage)
    print(f"Dataset shape: {df.shape}")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nMissing values:\n{df.isnull().sum()}")
    print(f"\nTarget distribution:\n{df[TARGET].value_counts()}")

    return df


if __name__ == "__main__":
    df = load_data()
    print("\n✅ Data loaded successfully!")
