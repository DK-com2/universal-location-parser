#!/usr/bin/env python3
"""
Google Timeline & GPX Parser - メインスクリプト
dataディレクトリ内の全JSONファイルとGPXファイルを処理して統合CSVを出力
"""

import sys
import os
from datetime import datetime

# モジュールのインポート
from modules.file_handler import find_all_files, load_json_file, get_username_from_filename, validate_json_data, validate_gpx_file
from modules.json_parser import parse_json_data
from modules.gpx_parser import parse_gpx_file
from modules.data_converter import convert_records_to_dataframe, sort_dataframe_by_time, combine_dataframes
from modules.csv_exporter import export_to_csv, print_summary, validate_output_data
from config import OUTPUT_FILE, DEBUG
from modules import kml_parser
import pandas as pd


def process_json_files(json_files):
    """JSONファイルを処理"""
    processed_dataframes = []
    processed_count = 0
    
    for i, json_file in enumerate(json_files, 1):
        print(f"\n[JSON {i}/{len(json_files)}] {os.path.basename(json_file)}")
        
        # ファイル読み込み
        data = load_json_file(json_file)
        if data is None:
            continue
        
        # データ妥当性チェック
        if not validate_json_data(data):
            if DEBUG:
                print("   ❌ 無効なJSONデータ形式")
            continue
        
        # ユーザー名生成
        username = get_username_from_filename(json_file)
        
        # JSON解析
        records = parse_json_data(data, username)
        if not records:
            continue
        
        # DataFrame変換
        df = convert_records_to_dataframe(records)
        if df.empty:
            continue
        
        processed_dataframes.append(df)
        processed_count += 1

        if DEBUG:
            print(f"   ✅ {len(df)} レコード抽出完了")
    
    return processed_dataframes, processed_count


def process_gpx_files(gpx_files):
    """GPXファイルを処理"""
    processed_dataframes = []
    processed_count = 0
    
    for i, gpx_file in enumerate(gpx_files, 1):
        print(f"\n[GPX {i}/{len(gpx_files)}] {os.path.basename(gpx_file)}")
        
        # ファイル妥当性チェック
        if not validate_gpx_file(gpx_file):
            if DEBUG:
                print("   ❌ 無効なGPXファイル形式")
            continue
        
        # ユーザー名生成
        username = get_username_from_filename(gpx_file)
        
        # GPX解析
        records = parse_gpx_file(gpx_file, username)
        if not records:
            continue
        
        # DataFrame変換
        df = convert_records_to_dataframe(records)
        if df.empty:
            continue
        
        processed_dataframes.append(df)
        processed_count += 1

        if DEBUG:
            print(f"   ✅ {len(df)} レコード抽出完了")
    
    return processed_dataframes, processed_count


def main():
    """メイン処理"""
    print("🌐 Google Timeline & GPX Parser")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # 1. 全ファイルの検索
    print("\n📁 ファイルを検索中...")
    all_files = find_all_files()
    json_files = all_files['json']
    gpx_files = all_files.get('gpx', [])
    kml_files = all_files.get('kml', [])
    
    total_files = len(json_files) + len(gpx_files) + len(kml_files)
    
    if total_files == 0:
        print("❌ 処理するファイルが見つかりません")
        print(f"   dataディレクトリ({os.path.abspath('data')})にファイルを配置してください")
        return
    
    print(f"📊 発見ファイル: JSON {len(json_files)}個, GPX {len(gpx_files)}個, KML/KMZ {len(kml_files)}個")

    all_dataframes = []
    total_processed = 0

    # 2. JSONファイルの処理
    if json_files:
        print(f"\n🔄 JSON処理: {len(json_files)}個のファイルを処理中...")
        json_dataframes, json_processed = process_json_files(json_files)
        all_dataframes.extend(json_dataframes)
        total_processed += json_processed
        print(f"✅ JSON処理完了: {json_processed}/{len(json_files)}個のファイルを処理")

    # GPXファイルの処理
    if gpx_files:
        print(f"\n🏔️ GPX処理: {len(gpx_files)}個のファイルを処理中...")
        gpx_dataframes, gpx_processed = process_gpx_files(gpx_files)
        all_dataframes.extend(gpx_dataframes)
        total_processed += gpx_processed
        print(f"✅ GPX処理完了: {gpx_processed}/{len(gpx_files)}個のファイルを処理")

    # KMLファイルの処理
    if kml_files:
        print(f"\n🗺️ KML/KMZ処理: {len(kml_files)}個のファイルを処理中...")
        kml_processed = 0
        for i, kml_file in enumerate(kml_files, 1):
            print(f"[KML {i}/{len(kml_files)}] {os.path.basename(kml_file)}")
            ext = os.path.splitext(kml_file)[1].lower()
            if ext in {".kml", ".kmz"}:
                try:
                    username = get_username_from_filename(kml_file)
                    records = kml_parser.parse_kml_file(kml_file, username=username)
                    df = convert_records_to_dataframe(records)  # 正規化
                    if not df.empty:
                        all_dataframes.append(df)
                        kml_processed += 1
                        if DEBUG:
                            print(f"   ✅ {len(df)} レコード抽出完了")
                except Exception as exc:
                    print(f"   ❌ KML解析エラー: {exc}")
        print(f"✅ KML/KMZ処理完了: {kml_processed}/{len(kml_files)}個のファイルを処理")
        total_processed += kml_processed

    # 3. データ統合
    if not all_dataframes:
        print("\n❌ 有効なデータが見つかりませんでした")
        return
    
    print(f"\n🔗 {total_processed}個のファイルからデータを統合中...")
    combined_df = combine_dataframes(all_dataframes)
    
    if combined_df.empty:
        print("❌ 統合後のデータが空です")
        return
    
    # 4. 時間ソート
    print("\n⏰ 時間順ソート中...")
    sorted_df = sort_dataframe_by_time(combined_df)
    
    # 5. 出力データ検証
    if not validate_output_data(sorted_df):
        print("❌ 出力データの検証に失敗しました")
        return
    
    # 6. CSV出力
    print(f"\n💾 CSV出力中...")
    output_file = export_to_csv(sorted_df, OUTPUT_FILE)
    
    if output_file:
        # 7. 結果サマリー表示
        end_time = datetime.now()
        processing_time = end_time - start_time
        
        print_summary(sorted_df, output_file)
        
        # GPXデータソース別統計
        if '_gpx_data_source' in sorted_df.columns:
            gpx_data = sorted_df[sorted_df['type'].str.startswith('gpx', na=False)]
            if not gpx_data.empty:
                print("\n🏔️ GPXデータソース別統計:")
                source_counts = gpx_data['_gpx_data_source'].value_counts()
                for source, count in source_counts.items():
                    print(f"   - {source}: {count:,}件")

        print(f"\n⏱️ 処理時間: {processing_time.total_seconds():.2f}秒")
        print("🎉 統合処理完了!")
    else:
        print("❌ CSV出力に失敗しました")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 処理が中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)
