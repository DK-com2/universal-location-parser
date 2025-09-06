import pandas as pd
from modules.data_converter import combine_dataframes


def test_concat_drops_all_na_columns_and_preserves_non_na():
    # DF1 has columns A (all NA), B (values)
    df1 = pd.DataFrame({
        'A': [None, None],
        'B': [1, 2]
    })
    # DF2 has columns A (all NA), C (values)
    df2 = pd.DataFrame({
        'A': [None, None],
        'C': ['x', 'y']
    })

    combined = combine_dataframes([df1, df2])

    # Column A is all NA in both -> should be dropped prior to concat
    assert 'A' not in combined.columns

    # Columns B and C should be present and values preserved
    assert 'B' in combined.columns
    assert 'C' in combined.columns

    # 4 rows total
    assert len(combined) == 4

    # Values are preserved
    assert combined['B'].dropna().tolist() == [1, 2]
    assert combined['C'].dropna().tolist() == ['x', 'y']
