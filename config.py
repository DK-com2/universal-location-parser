# Google Timeline & GPX Parser - 設定ファイル

# ディレクトリパス
DATA_DIR = "data"
OUTPUT_FILE = "timeline_output.csv"

# ユーザー名設定（シンプルに固定）
USERNAME = "testuser"

# CSV出力カラム定義（GPX対応拡張）
CSV_COLUMNS = [
    "type",
    "start_time", 
    "end_time",
    "point_time",
    "latitude",
    "longitude",
    "visit_probability",
    "visit_placeId", 
    "visit_semanticType",
    "activity_distanceMeters",
    "activity_type", 
    "activity_probability",
    "username",
    # GPX用追加フィールド
    "_gpx_data_source",
    "_gpx_track_name",
    "_gpx_elevation",
    "_gpx_speed",
    "_gpx_point_sequence"
]

# タイムゾーン設定
INPUT_TIMEZONE = "Asia/Tokyo"
OUTPUT_TIMEZONE = "UTC"

# サポートされるファイル形式（GPX追加）
SUPPORTED_EXTENSIONS = [".json", ".kml", ".kmz"]  # 参考用
GPX_EXTENSIONS = [".gpx", ".GPX"]  # 参考用

# ファイル種別ごとの拡張子リスト
JSON_EXTS = [".json"]
GPX_EXTS  = [".gpx", ".GPX"]
KML_EXTS  = [".kml", ".kmz", ".KML", ".KMZ"]

# デバッグモード
DEBUG = True

# GPX処理設定
GPX_CONFIG = {
    # アクティビティ分類しきい値
    "speed_thresholds": {
        "walking_max": 4,      # 4km/h未満 = 歩行
        "hiking_max": 6,       # 6km/h未満 = ハイキング（標高差考慮）
        "running_max": 15,     # 15km/h未満 = ランニング
        "cycling_max": 40,     # 40km/h未満 = サイクリング
        "driving_min": 40       # 40km/h以上 =運転
    },
    
    # 標高差による判定
    "elevation_thresholds": {
        "hiking_min_gain": 100  # 100m以上の標高差 = ハイキング
    },
    
    # データソース別デフォルト設定
    "data_source_defaults": {
        "yamap": {
            "default_activity": "hiking",
            "semantic_type": "Mountain"
        },
        "garmin": {
            "default_activity": "unknown",
            "semantic_type": "Sports"
        },
        "gpx": {
            "default_activity": "unknown",
            "semantic_type": "Other"
        }
    }
}
