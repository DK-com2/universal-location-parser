# Google Timeline & GPX Parser

Google TimelineデータとGPXファイルを統合処理する包括的なパーサーです。

## 🌟 新機能（2025年7月更新）

### 🗺️ KML/KMZ対応追加 ⭐ (最新)
- **Google Earth形式**: KML/KMZファイルの読み込み・解析
- **gx:Track要素**: タイムスタンプ付きトラックデータ
- **Placemarkサポート**: ポイント・ライン・複合ジオメトリ
- **KMZ自動展開**: ZIP圧縮されたKMLファイルの自動処理

### 🏔️ GPX対応追加
- **YAMAP**: 登山・ハイキングデータ
- **Garmin**: 各種スポーツアクティビティ
- **汎用GPX**: その他のGPSアプリからのエクスポート

### 🤖 インテリジェント分類
- ファイル名パターンによる自動判定
- 速度・標高パターンによるアクティビティ分類
- カスタマイズ可能な分類しきい値

### 📊 統合分析
- Timeline + GPX + KML/KMZ データの統一CSV出力
- データタイプ別統計
- 時系列での完全統合

## 🚨 貢献者を求めています！

このプロジェクトはオープンソースです。新しいデータ形式の対応、機能追加、バグ修正にご協力いただける方を募集しています。特に以下の分野の貢献を歓迎します。

- 新しいGPSデバイス・アプリの対応
- データの視覚化機能
- アクティビティ分類精度の改善
- 多言語対応

貢献方法については、[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

## プロジェクトの目標

このプロジェクトの目標は、あらゆる位置情報データ（タイムラインやGPSログなど）を1つの表にまとめて扱えるようにすることです。将来は [Pathfinder](https://pathfinder.dk-core.com/) の開発に役立つ汎用的なデータベースとして活用します。

## 📁 プロジェクト構造

```
timeline/
├── main.py                    # 従来のJSON専用処理
├── main_unified.py           # 新しい統合処理（JSON + GPX + KML/KMZ）⭐
├── config.py                 # 設定ファイル（GPX/KML対応拡張済み）
├── test_config.py            # 設定テストスクリプト ⭐
├── modules/                  # 機能別モジュール
│   ├── __init__.py
│   ├── file_handler.py       # ファイル操作（JSON + GPX + KML/KMZ対応）
│   ├── json_parser.py        # Google Timeline解析
│   ├── gpx_parser.py         # GPX解析 ⭐
│   ├── kml_parser.py         # KML/KMZ解析 ⭐
│   ├── data_converter.py     # データ変換（GPX/KML拡張対応）
│   └── csv_exporter.py       # CSV出力・統計
├── data/                     # 入力フォルダ（Git管理外）
│   ├── *.json               # Google Timeline JSONファイル
│   ├── *.gpx                # GPXファイル ⭐
│   ├── *.kml                # KMLファイル ⭐
│   └── *.kmz                # KMZファイル ⭐
├── sample_data/              # サンプルデータ
├── timeline_output.csv       # 統合出力ファイル
└── README_EXTENDED.md        # 詳細ドキュメント ⭐
```

## 🚀 使用方法

### 基本セットアップ
```bash
# 仮想環境を有効化（初回のみ）
python -m venv venv
source venv/bin/activate  # Linuxの場合
venv\Scripts\activate     # Windowsの場合

# 依存パッケージのインストール（初回のみ）
pip install -r requirements.txt
```

### データファイル配置
```bash
# Google TimelineのJSONファイル
cp your_timeline.json data/

# GPXファイル（YAMAP、Garmin等）
cp yamap_activity.gpx data/
cp garmin_activity.gpx data/

# KML/KMZファイル（Google Earth等）
cp track.kml data/
cp archive.kmz data/
```

### 実行方法

#### 🆕 推奨: 統合処理
```bash
# JSON + GPX + KML/KMZ を処理
python main_unified.py
```

#### 従来: JSON専用処理
```bash
# JSONファイルのみを処理
python main.py
```

### 結果確認
- `timeline_output.csv` が生成されます
- 時間順にソートされた統合データが出力されます

### 設定テスト
```bash
# 設定ファイルの動作確認
python test_config.py
```

## 📋 サポートされているデータ形式

### ✅ 現在対応済み

#### Google Timeline
- **Android形式**: `semanticSegments` 構造のJSONファイル
- **iPhone形式**: `startTime` 構造のJSONファイル

#### GPX形式 ⭐
- **YAMAP**: 登山・ハイキングデータ（`yamap_*.gpx`）
- **Garmin**: 各種スポーツアクティビティ（`activity_*.gpx`）
- **汎用GPX**: その他のGPSアプリからのエクスポート

#### KML/KMZ形式 ⭐
- **KML**: Point/LineString、TimeStamp/TimeSpan、`gx:Track` に対応
- **KMZ**: `doc.kml` がない場合は、最初に見つかった `.kml` を読み込みます
- 時刻の優先度: `point_time > start_time > end_time`

### 🔮 今後対応予定
- Strava API連携
- Apple Health GPS データ
- その他のGPSトラッカーアプリ

## 🧩 各モジュールの機能

### config.py ⭐ (GPX/KML対応拡張)
- **基本設定**: ディレクトリパス、ファイル名、ユーザー設定
- **CSV出力設定**: 統合カラム定義（Timeline + GPX/KML）
- **GPX処理設定**: アクティビティ分類しきい値、データソース設定
- **タイムゾーン設定**: 入力・出力タイムゾーン

### file_handler.py ⭐ (GPX/KML対応拡張)
- JSONファイル検索・読み込み（既存）
- **GPX/KML/KMZファイル検索・読み込み** (新規)
- **統合ファイル検索** (新規)
- 複数エンコーディング対応
- ファイル形式検証

### gpx_parser.py ⭐
- **XML解析**: GPXファイルの構造解析
- **データ抽出**: トラックポイント、ウェイポイント、メタデータ
- **速度計算**: 連続ポイント間の移動速度算出
- **アクティビティ判定**: ファイル名・内容・パターンによる自動分類
- **セマンティック分類**: 用途別カテゴリ割り当て

### kml_parser.py ⭐
- **KML/KMZ解析**: Placemark/Folder/Document対応、`gx:Track`の時刻整合
- **タイム抽出**: TimeStamp/TimeSpan/Track時刻、欠損時のフォールバック
- **幾何抽出**: Point/LineString/Trackの座標展開

### json_parser.py (既存維持)
- Android/iPhone形式の自動判別
- visit/activity/timelinePathの抽出
- 座標・時刻データの抽出

### data_converter.py ⭐ (GPX/KML拡張対応)
- タイムスタンプのUTC統一
- 数値データの正規化（Timeline + GPX/KML）
- **GPX特有フィールド**の処理
- DataFrame結合・時間順ソート
- **統合統計情報**生成

### csv_exporter.py ⭐ (GPX/KML対応拡張)
- **統合CSVファイル出力**（Timeline + GPX + KML/KMZ）
- データ検証・品質チェック
- **詳細な結果サマリー**（データタイプ別・ソース別統計）

## 📊 統合データ構造

### 共通フィールド
```csv
type,start_time,end_time,point_time,latitude,longitude,activity_type,username
```

### Timeline特有フィールド
```csv
visit_probability,visit_placeId,visit_semanticType,activity_distanceMeters,activity_probability
```

### GPX特有フィールド ⭐
```csv
_gpx_data_source,_gpx_track_name,_gpx_elevation,_gpx_speed,_gpx_point_sequence
```

### KML/KMZ特有フィールド ⭐
```csv
elevation,kml_source_type,kml_element_type,kml_placemark_name
```

## 🎯 アクティビティ自動分類

### 分類ロジック
1. **ファイル名判定**（最優先）
   - `yamap_*.gpx` → hiking
   - `*run*.gpx` → running
   - `*bike*.gpx` → cycling

2. **トラック名判定**
   - 「○○山」「○○岳」 → hiking
   - 「ランニング」「run」 → running

3. **移動パターン判定**（config.py設定値使用）
   - 速度 < 4km/h → walking
   - 速度 < 6km/h + 標高差 > 100m → hiking
   - 6-15km/h → running
   - 15-40km/h → cycling

### カスタマイズ可能な設定
```python
# config.py で調整可能
GPX_CONFIG = {
    "speed_thresholds": {
        "walking_max": 4,
        "hiking_max": 6,
        "running_max": 15,
        "cycling_max": 40
    },
    "elevation_thresholds": {
        "hiking_min_gain": 100
    }
}
```

## ⏱️ タイムゾーン仕様

- 入力の時刻文字列がタイムゾーンなし（naive）の場合は `INPUT_TIMEZONE` として解釈
- tz付きはそのまま受け取り、`OUTPUT_TIMEZONE` に変換
- すべての時刻は最終的に `OUTPUT_TIMEZONE` に変換したうえで tz情報を外した「naive UTC相当」で統一
- 時系列ソートの優先度は `point_time > start_time > end_time`

## 🔍 データ分析例

```python
import pandas as pd

# 統合データの読み込み
df = pd.read_csv('timeline_output.csv')

# Google Timelineデータのみ
timeline_data = df[df['type'].str.contains('visit|activity')]

# GPXデータのみ
gpx_data = df[df['type'].str.startswith('gpx')]

# KMLデータのみ
kml_data = df[df['type'].str.startswith('kml')]

# 登山データの分析
hiking_data = df[df['activity_type'] == 'hiking']
print(f"登山回数: {hiking_data['_gpx_track_name'].nunique()}回")

# 月別アクティビティ統計
monthly_stats = df.groupby([
    df['start_time'].dt.to_period('M'), 
    'activity_type'
]).size()
```

## 🛠️ 新しいGPSデバイス対応方法

### 1. データソース検出の追加
```python
# modules/gpx_parser.py の detect_data_source() を拡張
def detect_data_source(filename):
    filename_lower = filename.lower()
    
    if 'yamap' in filename_lower:
        return 'yamap'
    elif 'strava' in filename_lower:  # 新規追加
        return 'strava'
    elif 'suunto' in filename_lower:  # 新規追加
        return 'suunto'
    # ... 他のデバイス追加
```

### 2. 設定の追加
```python
# config.py の GPX_CONFIG に追加
"data_source_defaults": {
    "strava": {
        "default_activity": "unknown",
        "semantic_type": "Sports"
    },
    "suunto": {
        "default_activity": "unknown", 
        "semantic_type": "Sports"
    }
}
```

## 📈 処理結果例

```bash
🌐 Google Timeline & GPX Parser
==================================================

📁 ファイルを検索中...
📊 発見ファイル: JSON 2個, GPX 3個, KML 1個, KMZ 1個

🔄 JSON処理: 2個のファイルを処理中...
✅ JSON処理完了: 2/2個のファイルを処理

🏔️ GPX処理: 3個のファイルを処理中...
✅ GPX処理完了: 3/3個のファイルを処理

🌍 KML/KMZ処理: 2個のファイルを処理中...
✅ KML/KMZ処理完了: 2/2個のファイルを処理

🔗 7個のファイルからデータを統合中...
⏰ 時間順ソート中...
💾 CSV出力中...

📈 データタイプ別統計:
   - visit: 234件
   - gpx_trackpoint: 5,456件
   - kml_point: 120件
   - activity_start: 123件

🏔️ GPXデータソース別統計:
   - yamap: 2,456件
   - garmin: 1,834件

⏱️ 処理時間: 12.34秒
🎉 統合処理完了!
```

## 🧪 サンプルデータの使用

### 提供サンプル
```bash
sample_data/
├── sample_android.json      # Android Timeline
├── sample_iphone.json       # iPhone Timeline
├── sample_boundary.kml      # KML サンプル
└── (GPXサンプルは data/ に配置済み)

# サンプルを使った実行
cp sample_data/*.json data/
cp sample_data/*.kml data/
python main_unified.py
```

### リアルデータ使用
```bash
# 実際のデータディレクトリ
data/
├── yamap_2025-01-18_07_17.gpx      # YAMAP登山データ
├── activity_12303576279.gpx        # Garminアクティビティ
├── track.kml                       # Google Earth KML
├── archive.kmz                     # KMZ アーカイブ
├── timeline_android.json           # Android Timeline
└── timeline_iphone.json            # iPhone Timeline
```

## 🔧 設定カスタマイズ

### ユーザー名設定
```python
# config.py
USERNAME = "your_username"  # デフォルトユーザー名変更
```

### アクティビティ分類調整
```python
# config.py - 登山判定を緩くする例
GPX_CONFIG = {
    "speed_thresholds": {
        "hiking_max": 8,  # 8km/hまで登山とする
    },
    "elevation_thresholds": {
        "hiking_min_gain": 50  # 50m以上の標高差で登山
    }
}
```

### CSV出力カラム調整
```python
# config.py - 不要なカラムを除外
CSV_COLUMNS = [
    "type", "start_time", "latitude", "longitude", 
    "activity_type", "_gpx_elevation"  # 必要な列のみ
]
```

## 🌟 特徴

### 🔄 統合アーキテクチャ
- **既存機能保護**: JSON処理は従来通り動作
- **新機能追加**: GPX/KML処理をシームレスに統合
- **下位互換性**: 既存のワークフローに影響なし

### 🤖 インテリジェント処理
- **自動形式判別**: JSON/GPX/KML/KMZを自動認識
- **アクティビティ分類**: ファイル名・内容・パターンで自動判定
- **データ品質管理**: 異常値検出・除外

### ⚙️ 柔軟な設定管理
- **一元設定**: `config.py`で全設定を管理
- **カスタマイズ可能**: しきい値・分類ルールを調整可能
- **拡張性**: 新しいデバイス・ルールを簡単追加

### 🛡️ 強力なエラーハンドリング
- **複数エンコーディング対応**: UTF-8、Shift_JIS等
- **段階的検証**: ファイル→形式→内容の多層チェック
- **詳細ログ**: デバッグモードでの詳細情報表示

## 📚 ドキュメント

- **[README_EXTENDED.md](README_EXTENDED.md)**: より詳細な技術仕様・データ分析例
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: 貢献方法・開発ガイドライン
- **[CHANGELOG.md](CHANGELOG.md)**: 変更履歴・仕様変更の明文化

## 🔮 将来の拡張計画

### Phase 1: データソース拡張
- Strava API連携
- Apple Health GPS データ
- Suunto、Polar等のデバイス対応

### Phase 2: 高度な分析機能
- 移動パターン分析
- 健康データとの統合
- 機械学習による行動予測

### Phase 3: 可視化・インターフェース
- Webベースのダッシュボード
- インタラクティブマップ
- リアルタイム分析

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🤝 貢献方法

プロジェクトへの貢献を歓迎します！

1. **Issue報告**: バグや機能要望
2. **Pull Request**: コード改善・新機能追加
3. **ドキュメント**: 使用方法・チュートリアルの改善
4. **テスト**: 新しいデバイス・データ形式でのテスト

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。
