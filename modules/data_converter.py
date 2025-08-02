"""
データ変換モジュール
時間変換、座標データの統一、データ型の正規化
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from config import INPUT_TIMEZONE, OUTPUT_TIMEZONE, DEBUG


def convert_timestamp_to_utc(timestamp_str: str) -> pd.Timestamp:
    """タイムスタンプ文字列をUTCのnaive datetimeに変換"""
    if not timestamp_str:
        return None
    try:
        dt = pd.to_datetime(timestamp_str, errors='coerce')
        if pd.isna(dt):
            return None
        # まずUTCに揃える
        if dt.tz is None:
            dt = dt.tz_localize(OUTPUT_TIMEZONE)
        else:
            dt = dt.tz_convert(OUTPUT_TIMEZONE)
        # 最後にnaive化
        return dt.tz_localize(None)
    except Exception as e:
        if DEBUG:
            print(f"   ⚠️ 時間変換エラー: {timestamp_str!r} -> {e}")
        return None


def normalize_numeric_value(value) -> float:
    """数値データの正規化"""
    if value is None or value == '':
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def convert_records_to_dataframe(records: List[Dict]) -> pd.DataFrame:
    """レコードリストをDataFrameに変換して正規化"""
    if not records:
        return pd.DataFrame()
    
    df = pd.DataFrame(records)

    if DEBUG:
        print(f"   🔄 {len(df)} レコードを変換中...")
    
    # 時間カラムの変換
    time_columns = ['start_time', 'end_time', 'point_time']
    for col in time_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_timestamp_to_utc)
    
    # 数値カラムの変換（Timeline用）
    numeric_columns = [
        'latitude', 'longitude', 'activity_distanceMeters', 
        'visit_probability', 'activity_probability'
    ]
    
    # GPX用の追加数値カラム
    gpx_numeric_columns = [
        '_gpx_elevation', '_gpx_speed', '_gpx_point_sequence'
    ]
    
    all_numeric_columns = numeric_columns + gpx_numeric_columns
    
    for col in all_numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(normalize_numeric_value)
    
    # NaN を None に置換
    df = df.replace({np.nan: None})
    
    if DEBUG:
        print(f"   ✅ データ変換完了")
    
    return df


def _to_naive_utc(series: pd.Series) -> pd.Series:
    """文字列/Timestamp混在 → UTC→naive→datetime64[ns] へ整形"""
    dt = pd.to_datetime(series, utc=True, errors="coerce")
    return dt.dt.tz_convert(None)


def sort_dataframe_by_time(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrameを時間順にソート"""
    if df.empty:
        return df

    if DEBUG:
        print("   🔄 時間順ソート中...")

    # すべての時間列をUTC naiveなdatetime64[ns]に統一
    for col in ["point_time", "start_time", "end_time"]:
        if col in df.columns:
            df[col] = _to_naive_utc(df[col])

    # ソート用の時間列を作成（優先順位: point_time > start_time > end_time）
    sort_time = df.get('point_time', pd.Series(index=df.index, dtype='datetime64[ns]'))
    
    if 'start_time' in df.columns:
        sort_time = sort_time.fillna(df['start_time'])
    
    if 'end_time' in df.columns:
        sort_time = sort_time.fillna(df['end_time'])

    # ソート実行
    if not sort_time.isna().all():
        sorted_indices = sort_time.sort_values().index
        df_sorted = df.loc[sorted_indices].reset_index(drop=True)

        if DEBUG:
            print(f"   ✅ 時間順ソート完了")

        return df_sorted
    else:
        if DEBUG:
            print("   ⚠️ ソート可能な時間データなし")
        return df


def combine_dataframes(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """複数のDataFrameを結合"""
    if not dataframes:
        return pd.DataFrame()

    if DEBUG:
        total_records = sum(len(df) for df in dataframes)
        print(f"🔗 {len(dataframes)}個のDataFrameを結合中... (総{total_records}レコード)")
    
    combined_df = pd.concat(dataframes, ignore_index=True)

    if DEBUG:
        print(f"✅ 結合完了: {len(combined_df)} レコード")
    
    return combined_df


def get_dataframe_summary(df: pd.DataFrame) -> Dict:
    """DataFrameの要約情報を取得"""
    if df.empty:
        return {"total_records": 0}

    # 時間カラムをリストに集めてからconcat
    time_series = []
    for col in ["point_time", "start_time", "end_time"]:
        if col in df.columns:
            time_series.append(df[col])
    
    _times = pd.concat(time_series) if time_series else pd.Series(dtype='datetime64[ns]')

    summary = {
        "total_records": len(df),
        "data_types": df['type'].value_counts().to_dict() if 'type' in df.columns else {},
        "users": df['username'].value_counts().to_dict() if 'username' in df.columns else {},
        "time_range": {
            "start": _times.min(),
            "end": _times.max(),
        },
        "location_records": df[['latitude', 'longitude']].notna().all(axis=1).sum() if all(col in df.columns for col in ['latitude', 'longitude']) else 0
    }

    # GPXデータの特別統計
    gpx_data = df[df['type'].str.startswith('gpx', na=False)] if 'type' in df.columns else pd.DataFrame()
    if not gpx_data.empty:
        summary["gpx_stats"] = {
            "total_gpx_records": len(gpx_data),
            "gpx_data_sources": gpx_data['_gpx_data_source'].value_counts().to_dict() if '_gpx_data_source' in gpx_data.columns else {},
            "gpx_tracks": gpx_data['_gpx_track_name'].nunique() if '_gpx_track_name' in gpx_data.columns else 0,
            "elevation_range": {
                "min": gpx_data['_gpx_elevation'].min() if '_gpx_elevation' in gpx_data.columns else None,
                "max": gpx_data['_gpx_elevation'].max() if '_gpx_elevation' in gpx_data.columns else None
            } if '_gpx_elevation' in gpx_data.columns else None
        }

    return summary
