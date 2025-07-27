import numpy as np
import pandas as pd

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Make infinite values safe
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # Optional: flag rows with critical NaNs for reporting
    df['__row_has_nan__'] = df.isna().any(axis=1)
    return df
