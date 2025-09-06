"""
CSV出力モジュール
時間ソート済みデータのCSV書き込み
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict
from config import OUTPUT_FILE, CSV_COLUMNS, DEBUG


def export_to_csv(df: pd.DataFrame, output_file: str = None) -> str:
    """DataFrameをCSVファイルに出力"""
    
    if df.empty:
        if DEBUG:
            print("❌ 出力するデータがありません")
        return None
    
    # 出力ファイル名の決定
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"timeline_{timestamp}.csv"
    
    try:
        # カラム順序を統一
        output_columns = [col for col in CSV_COLUMNS if col in df.columns]
        df_output = df[output_columns]
        
        # CSV出力
        df_output.to_csv(output_file, index=False, encoding='utf-8')
        
        file_size = os.path.getsize(output_file)
        
        if DEBUG:
            print(f"✅ CSV出力完了:")
            print(f"   📄 ファイル: {output_file}")
            print(f"   📊 レコード数: {len(df_output):,}")
            print(f"   💾 ファイルサイズ: {file_size:,} bytes")
        
        return output_file
        
    except Exception as e:
        if DEBUG:
            print(f"❌ CSV出力エラー: {e}")
        return None


def print_summary(df: pd.DataFrame, output_file: str):
    """処理結果のサマリーを表示"""
    if df.empty:
        print("\n📋 処理結果サマリー:")
        print("   ❌ 処理できるデータがありませんでした")
        return

    print("\n📋 処理結果サマリー:")
    print(f"   📊 総レコード数: {len(df):,}")

    # データタイプ別集計
    if 'type' in df.columns:
        type_counts = df['type'].value_counts()
        print("   📱 データタイプ別:")
        for data_type, count in type_counts.items():
            print(f"      - {data_type}: {count:,}")

    # ユーザー別集計
    if 'username' in df.columns:
        user_counts = df['username'].value_counts()
        print("   👤 ユーザー別:")
        for username, count in user_counts.items():
            print(f"      - {username}: {count:,}")

    # 時間範囲（get_dataframe_summaryの値を利用）
    from modules.data_converter import get_dataframe_summary
    summary = get_dataframe_summary(df)
    time_range = summary.get('time_range', {})
    time_start = time_range.get('start')
    time_end = time_range.get('end')
    print("   ⏰ 時間範囲:", end=" ")
    if time_start and time_end:
        print(f"{time_start} ～ {time_end}")
    else:
        print("(データなし)")
    
    # 位置情報
    location_data = df.dropna(subset=['latitude', 'longitude']) if all(col in df.columns for col in ['latitude', 'longitude']) else pd.DataFrame()
    if not location_data.empty:
        print(f"   🗺️ 位置情報付きレコード: {len(location_data):,}")
        print(f"   📍 緯度範囲: {location_data['latitude'].min():.6f} ～ {location_data['latitude'].max():.6f}")
        print(f"   📍 経度範囲: {location_data['longitude'].min():.6f} ～ {location_data['longitude'].max():.6f}")
    
    # 活動データ
    activity_data = df[df['activity_type'].notna()] if 'activity_type' in df.columns else pd.DataFrame()
    if not activity_data.empty:
        activity_counts = activity_data['activity_type'].value_counts()
        print("   🚶 活動タイプ別:")
        for activity, count in activity_counts.items():
            print(f"      - {activity}: {count:,}")
        
        total_distance = activity_data['activity_distanceMeters'].sum() if 'activity_distanceMeters' in activity_data.columns else 0
        if total_distance and total_distance > 0:
            print(f"   📏 総移動距離: {total_distance:,.0f} メートル ({total_distance/1000:.1f} km)")
    
    if output_file:
        print(f"   💾 出力ファイル: {output_file}")


def validate_output_data(df: pd.DataFrame) -> bool:
    """出力データの妥当性をチェック"""
    if df.empty:
        return False
    
    # 必須カラムの存在チェック
    required_columns = ['type', 'username']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        if DEBUG:
            print(f"⚠️ 必須カラムが不足: {missing_columns}")
        return False
    
    # データの基本チェック
    if df['type'].isna().all():
        if DEBUG:
            print("⚠️ typeカラムがすべて空です")
        return False
    
    if DEBUG:
        print("✅ 出力データの妥当性チェック完了")
    
    return True
