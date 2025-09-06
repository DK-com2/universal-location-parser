"""
ファイル操作モジュール
JSONファイルの検索、読み込み、エラーハンドリング
"""

import os
import json
import glob
from typing import List, Union, Dict, Any
from config import DATA_DIR, SUPPORTED_EXTENSIONS, DEBUG, USERNAME, JSON_EXTS, GPX_EXTS, KML_EXTS
from pathlib import Path


def _glob_exts(base_dir: Path, exts: list) -> list:
    """
    指定ディレクトリ以下から指定拡張子のファイルを再帰的に検索する。
    Args:
        base_dir (Path): 検索対象ディレクトリ。
        exts (list): 検索する拡張子リスト（例: ['.json', '.gpx']）。
    Returns:
        list: ファイルパスのリスト（重複なし、ソート済み）。
    """
    files = []
    for ext in exts:
        files.extend(base_dir.glob(f"**/*{ext}"))
    return sorted(set(str(f) for f in files))


def find_json_files(base_dir=DATA_DIR):
    """
    データディレクトリ内のJSONファイルを検索する。
    Args:
        base_dir (str or Path): 検索対象ディレクトリ。
    Returns:
        list: JSONファイルのパスリスト。
    Note:
        ディレクトリが存在しない場合は空リストを返す。
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        print(f"❌ データディレクトリが存在しません: {base_dir}")
        return []
    files = _glob_exts(base_dir, JSON_EXTS)
    
    if DEBUG:
        print(f"📁 {len(files)}個のJSONファイルを発見:")
        for file in files:
            print(f"   - {os.path.basename(file)}")
    
    return files


def find_gpx_files(base_dir=DATA_DIR):
    """
    データディレクトリ内のGPXファイルを検索する。
    Args:
        base_dir (str or Path): 検索対象ディレクトリ。
    Returns:
        list: GPXファイルのパスリスト。
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        print(f"❌ データディレクトリが存在しません: {base_dir}")
        return []
    files = _glob_exts(base_dir, GPX_EXTS)
    
    if DEBUG:
        print(f"🏔️ {len(files)}個のGPXファイルを発見:")
        for file in files:
            print(f"   - {os.path.basename(file)}")
    
    return files


def find_kml_files(base_dir=DATA_DIR):
    """
    データディレクトリ内のKML/KMZファイルを検索する。
    Args:
        base_dir (str or Path): 検索対象ディレクトリ。
    Returns:
        list: KML/KMZファイルのパスリスト。
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        print(f"❌ データディレクトリが存在しません: {base_dir}")
        return []
    files = _glob_exts(base_dir, KML_EXTS)

    # 他形式(JSON/GPX)と同様にデバッグ出力を揃える
    if DEBUG:
        print(f"🗺️ {len(files)}個のKML/KMZファイルを発見:")
        for file in files:
            print(f"   - {os.path.basename(file)}")
    
    return files


def find_all_files(base_dir: Path = Path(DATA_DIR)) -> dict:
    """
    すべてのサポートされているファイルを検索する（KML/KMZも含む）。
    Args:
        base_dir (Path): 検索対象ディレクトリ。
    Returns:
        dict: 拡張子ごとのファイルリスト辞書。
    """
    return {
        "json": find_json_files(base_dir),
        "gpx": find_gpx_files(base_dir),
        "kml": find_kml_files(base_dir),
    }


def load_json_file(filepath) -> Union[Dict, List, None]:
    """
    JSONファイルを安全に読み込む（複数エンコーディング対応）。
    Args:
        filepath (str): 読み込み対象ファイルパス。
    Returns:
        dict, list, or None: パース済みデータ。失敗時はNone。
    Note:
        - ファイルサイズ0や空ファイルはNone。
        - utf-8, shift_jis, cp932等で順次デコードを試みる。
        - JSONDecodeErrorやUnicodeDecodeErrorは握りつぶして次のエンコーディングへ。
    """
    if DEBUG:
        print(f"📖 読み込み中: {os.path.basename(filepath)}")

    try:
        # ファイルサイズチェック
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            if DEBUG:
                print("   ❌ ファイルが空です")
            return None
        
        # 複数エンコーディングで試行
        encodings = ['utf-8', 'utf-8-sig', 'shift_jis', 'cp932']
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read().strip()

                if not content:
                    if DEBUG:
                        print("   ❌ ファイル内容が空です")
                    return None

                data = json.loads(content)
                if DEBUG:
                    print(f"   ✅ 読み込み成功 ({encoding})")
                return data
                
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError as e:
                if DEBUG:
                    print(f"   ❌ JSON解析エラー ({encoding}): {e}")
                continue
        
        if DEBUG:
            print("   ❌ 全エンコーディングで失敗")
        return None
        
    except Exception as e:
        if DEBUG:
            print(f"   ❌ ファイル読み込みエラー: {e}")
        return None


def get_username() -> str:
    """
    設定ファイルから固定ユーザー名を返す。
    Returns:
        str: ユーザー名。
    """
    return USERNAME


def get_username_from_filename(filepath: str) -> str:
    """
    ファイル名からユーザー名を抽出する。
    Args:
        filepath (str): 対象ファイルパス。
    Returns:
        str: 抽出されたユーザー名。見つからない場合は設定ファイルのユーザー名。
    Note:
        - "username-"や"user-"プレフィックス、アンダースコア区切り等に対応。
    """
    # ファイル名から基本名を取得（拡張子を除く）
    basename = os.path.basename(filepath)
    filename_without_ext = os.path.splitext(basename)[0]
    
    # ファイル名からユーザー名のパターンを識別
    # 1. ファイル名に「username-」または「user-」プレフィックスがある場合
    if filename_without_ext.lower().startswith("username-"):
        return filename_without_ext[9:]
    elif filename_without_ext.lower().startswith("user-"):
        return filename_without_ext[5:]
    
    # 2. アンダースコアで区切られた場合（例: username_date.json）
    parts = filename_without_ext.split('_')
    if len(parts) > 1:
        return parts[0]
    
    # 3. 特定のパターンが見つからない場合は設定ファイルのユーザー名を使用
    return get_username()


def validate_json_data(data: Union[Dict, List]) -> bool:
    """
    JSONデータの基本的な検証（Android/iPhone形式の判定）。
    Args:
        data (dict or list): 検証対象データ。
    Returns:
        bool: 有効な形式ならTrue。
    Note:
        - Android形式: dictで'semanticSegments'キーを持つ
        - iPhone形式: listで先頭要素に'startTime'キーを持つ
    """
    if data is None:
        return False
    
    if isinstance(data, dict) and 'semanticSegments' in data:
        return True  # Android形式
    
    if isinstance(data, list) and len(data) > 0 and 'startTime' in data[0]:
        return True  # iPhone形式
    
    return False


def validate_gpx_file(filepath: str) -> bool:
    """
    GPXファイルの基本的な検証（ヘッダー確認）。
    Args:
        filepath (str): 検証対象ファイルパス。
    Returns:
        bool: GPXファイルらしければTrue。
    Note:
        - 先頭1000文字に<?xml ... gpx>タグがあればOK。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # 最初の1000文字をチェック
        
        # 基本的なGPXヘッダーの確認
        return '<?xml' in content and ('gpx' in content.lower() or 'GPX' in content)
        
    except Exception:
        return False
