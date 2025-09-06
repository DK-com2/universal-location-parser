"""
データ変換モジュール
時間変換、座標データの統一、データ型の正規化
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from config import INPUT_TIMEZONE, OUTPUT_TIMEZONE, DEBUG


def convert_timestamp_to_utc(timestamp_str: str) -> pd.Timestamp:
    """タイムスタンプ文字列をUTCのnaive datetimeに変換
    - tzなし(naive)は INPUT_TIMEZONE として解釈
    - 最終的に OUTPUT_TIMEZONE に変換して tz情報を外す
    """
    if not timestamp_str:
        return None
    try:
        dt = pd.to_datetime(timestamp_str, errors='coerce')
        if pd.isna(dt):
            return None
        # タイムゾーン正規化
        if dt.tz is None:
            # 入力がnaive → 入力TZとしてlocalize
            dt = dt.tz_localize(INPUT_TIMEZONE)
        # 出力TZへ変換
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
    """混在データ(文字列/Timestamp/naive/tz-aware)を統一
    - naive→INPUT_TIMEZONE でlocalize
    - OUTPUT_TIMEZONEへ変換→naive化
    """
    # 個々に処理してシリーズを返す
    def _conv(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return None
        try:
            if not isinstance(x, pd.Timestamp):
                x = pd.to_datetime(x, errors='coerce')
            if pd.isna(x):
                return None
            if x.tz is None:
                x = x.tz_localize(INPUT_TIMEZONE)
            x = x.tz_convert(OUTPUT_TIMEZONE)
            return x.tz_localize(None)
        except Exception:
            return None
    return series.apply(_conv)


def sort_dataframe_by_time(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrameを時間順にソート (存在しない列を安全に扱う)"""
    if df.empty:
        return df

    if DEBUG:
        print("   🔄 時間順ソート中...")

    # すべての時間列をUTC naiveなdatetime64[ns]に統一（存在するもののみ）
    for col in ["point_time", "start_time", "end_time"]:
        if col in df.columns:
            df[col] = _to_naive_utc(df[col])

    # 各列が存在しない場合は NaT シリーズを用意
    def _safe_series(name: str) -> pd.Series:
        if name in df.columns:
            return df[name]
        # 長さ0対策（空DFは最初にreturnしているので len(df)>0 前提）
        return pd.Series([pd.NaT] * len(df), name=name)

    point_series = _safe_series("point_time")
    start_series = _safe_series("start_time")
    end_series = _safe_series("end_time")

    # 優先順位: point_time > start_time > end_time
    sort_time = point_series.fillna(start_series).fillna(end_series)

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
    """複数のDataFrameを結合
    - 空のDataFrameは除外
    - 全行NAの列は一時的に除去してから結合（pandasの将来仕様変更に備える）
    """
    if not dataframes:
        return pd.DataFrame()

    # 空DFを除外し、全NA列をドロップ（結合後に必要な列は他DFに値があれば自動で揃う）
    valid_dfs: List[pd.DataFrame] = []
    for df in dataframes:
        if isinstance(df, pd.DataFrame) and not df.empty:
            cleaned = df.dropna(axis=1, how='all')
            valid_dfs.append(cleaned)

    if not valid_dfs:
        return pd.DataFrame()

    if DEBUG:
        total_records = sum(len(df) for df in valid_dfs)
        print(f"🔗 {len(valid_dfs)}個のDataFrameを結合中... (総{total_records}レコード)")
    
    combined_df = pd.concat(valid_dfs, ignore_index=True, copy=False)

    if DEBUG:
        print(f"✅ 結合完了: {len(combined_df)} レコード")
    
    return combined_df


def get_dataframe_summary(df: pd.DataFrame) -> Dict:
    """DataFrameの要約情報を取得 (時間列が欠けるケースに対応)"""
    if df.empty:
        return {"total_records": 0}

    # 存在する時間列のみ連結
    time_series_list = []
    for name in ["point_time", "start_time", "end_time"]:
        s = df.get(name)
        if s is not None:
            time_series_list.append(s)
    if time_series_list:
        _times = pd.concat(time_series_list)
    else:
        _times = pd.Series([], dtype="datetime64[ns]")

    summary = {
        "total_records": len(df),
        "data_types": df['type'].value_counts().to_dict() if 'type' in df.columns else {},
        "users": df['username'].value_counts().to_dict() if 'username' in df.columns else {},
        "time_range": {
            "start": _times.min() if not _times.empty else None,
            "end": _times.max() if not _times.empty else None,
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
