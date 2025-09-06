"""
GPX解析モジュール
GPXファイルの読み込みと解析機能
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import math
from config import DEBUG, GPX_CONFIG


def parse_gpx_file(file_path: str, username: str) -> List[Dict]:
    """GPXファイルを解析してレコードリストを返す"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return parse_gpx_content(content, username, file_path)
        
    except Exception as e:
        if DEBUG:
            print(f"   ❌ GPXファイル読み込みエラー: {e}")
        return []


def parse_gpx_content(gpx_content: str, username: str, filename: str = "") -> List[Dict]:
    """GPXコンテンツを解析してレコードリストを返す"""
    try:
        # XML解析
        root = ET.fromstring(gpx_content)
        
        # 名前空間の処理
        namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        if root.tag.startswith('{'):
            namespace_uri = root.tag.split('}')[0][1:]
            namespace = {'gpx': namespace_uri}
        
        records = []
        
        # データソースの判定
        data_source = detect_data_source(filename)
        
        # トラックの処理
        tracks = root.findall('.//gpx:trk', namespace)
        for track_idx, track in enumerate(tracks):
            track_records = process_track(track, track_idx, namespace, username, data_source, filename)
            records.extend(track_records)
        
        # ウェイポイントの処理
        waypoints = root.findall('.//gpx:wpt', namespace)
        for wpt_idx, waypoint in enumerate(waypoints):
            wpt_record = process_waypoint(waypoint, wpt_idx, namespace, username, data_source)
            if wpt_record:
                records.append(wpt_record)

        if DEBUG:
            print(f"   📊 GPXレコード抽出: {len(records)}件")

        return records
        
    except ET.ParseError as e:
        if DEBUG:
            print(f"   ❌ GPX解析エラー: {e}")
        return []
    except Exception as e:
        if DEBUG:
            print(f"   ❌ GPX処理エラー: {e}")
        return []


def detect_data_source(filename: str) -> str:
    """ファイル名からデータソースを判定"""
    filename_lower = filename.lower()
    
    if 'yamap' in filename_lower:
        return 'yamap'
    elif 'garmin' in filename_lower or 'activity_' in filename_lower:
        return 'garmin'
    else:
        return 'gpx'


def process_track(track, track_idx: int, namespace: dict, username: str, data_source: str, filename: str) -> List[Dict]:
    """トラックを処理してレコードリストを返す"""
    records = []
    
    # トラック名の取得
    track_name_elem = track.find('gpx:name', namespace)
    track_name = track_name_elem.text if track_name_elem is not None else f"Track {track_idx + 1}"
    
    # トラックセグメントの処理
    segments = track.findall('.//gpx:trkseg', namespace)
    all_trackpoints = []
    
    for seg_idx, segment in enumerate(segments):
        trackpoints = segment.findall('gpx:trkpt', namespace)
        
        for pt_idx, point in enumerate(trackpoints):
            trackpoint_data = parse_trackpoint(point, namespace, pt_idx)
            if trackpoint_data:
                trackpoint_data.update({
                    'track_name': track_name,
                    'track_index': track_idx,
                    'segment_index': seg_idx
                })
                all_trackpoints.append(trackpoint_data)
    
    if not all_trackpoints:
        return records
    
    # 全体の開始・終了時刻を計算
    valid_times = [tp['point_time'] for tp in all_trackpoints if tp['point_time']]
    start_time = min(valid_times) if valid_times else None
    end_time = max(valid_times) if valid_times else None
    
    # アクティビティタイプの自動判定
    activity_type = classify_activity(filename, track_name, all_trackpoints)
    semantic_type = assign_semantic_type(activity_type, track_name)
    
    # 速度の計算
    calculate_speeds(all_trackpoints)
    
    # 各トラックポイントをレコードに変換
    for trackpoint in all_trackpoints:
        record = {
            "type": "gpx_trackpoint",
            "start_time": start_time,
            "end_time": end_time,
            "point_time": trackpoint['point_time'],
            "latitude": trackpoint['latitude'],
            "longitude": trackpoint['longitude'],
            "visit_probability": None,
            "visit_placeId": track_name,
            "visit_semanticType": semantic_type,
            "activity_distanceMeters": trackpoint.get('elevation'),  # 標高を距離フィールドに格納
            "activity_type": activity_type,
            "activity_probability": trackpoint.get('speed', 0) / 50 if trackpoint.get('speed') else None,  # 正規化された速度
            "username": username,
            # 追加情報（将来の拡張用）
            "_gpx_data_source": data_source,
            "_gpx_track_name": track_name,
            "_gpx_elevation": trackpoint.get('elevation'),
            "_gpx_speed": trackpoint.get('speed'),
            "_gpx_point_sequence": trackpoint['point_index']
        }
        records.append(record)
    
    return records


def process_waypoint(waypoint, wpt_idx: int, namespace: dict, username: str, data_source: str) -> Optional[Dict]:
    """ウェイポイントを処理してレコードを返す"""
    try:
        lat = float(waypoint.get('lat'))
        lon = float(waypoint.get('lon'))
        
        name_elem = waypoint.find('gpx:name', namespace)
        wpt_name = name_elem.text if name_elem is not None else f"Waypoint {wpt_idx + 1}"
        
        desc_elem = waypoint.find('gpx:desc', namespace)
        description = desc_elem.text if desc_elem is not None else None
        
        ele_elem = waypoint.find('gpx:ele', namespace)
        elevation = float(ele_elem.text) if ele_elem is not None else None
        
        time_elem = waypoint.find('gpx:time', namespace)
        point_time = None
        if time_elem is not None:
            try:
                point_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
            except:
                point_time = None
        
        return {
            "type": "gpx_waypoint",
            "start_time": point_time,
            "end_time": point_time,
            "point_time": point_time,
            "latitude": lat,
            "longitude": lon,
            "visit_probability": None,
            "visit_placeId": wpt_name,
            "visit_semanticType": "Waypoint",
            "activity_distanceMeters": elevation,
            "activity_type": "waypoint",
            "activity_probability": None,
            "username": username,
            # 追加情報
            "_gpx_data_source": data_source,
            "_gpx_track_name": wpt_name,
            "_gpx_elevation": elevation,
            "_gpx_speed": None,
            "_gpx_point_sequence": wpt_idx,
            "_gpx_description": description
        }
        
    except (ValueError, TypeError):
        return None


def parse_trackpoint(point, namespace: dict, point_index: int) -> Optional[Dict]:
    """トラックポイントを解析"""
    try:
        lat = float(point.get('lat'))
        lon = float(point.get('lon'))
        
        # 標高の取得
        ele_elem = point.find('gpx:ele', namespace)
        elevation = float(ele_elem.text) if ele_elem is not None else None
        
        # 時刻の取得
        time_elem = point.find('gpx:time', namespace)
        point_time = None
        if time_elem is not None:
            try:
                point_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
            except:
                point_time = None
        
        return {
            'latitude': lat,
            'longitude': lon,
            'elevation': elevation,
            'point_time': point_time,
            'point_index': point_index
        }
        
    except (ValueError, TypeError):
        return None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間の距離をメートルで計算（ハーバーサイン公式）"""
    R = 6371000  # 地球の半径（メートル）
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def calculate_speeds(trackpoints: List[Dict]) -> None:
    """トラックポイント間の速度を計算（km/h）"""
    for i in range(len(trackpoints)):
        if i == 0:
            trackpoints[i]['speed'] = 0
            continue
            
        try:
            prev_point = trackpoints[i-1]
            curr_point = trackpoints[i]
            
            if not all([prev_point.get('latitude'), prev_point.get('longitude'),
                       curr_point.get('latitude'), curr_point.get('longitude'),
                       prev_point.get('point_time'), curr_point.get('point_time')]):
                trackpoints[i]['speed'] = 0
                continue
            
            distance = haversine_distance(
                prev_point['latitude'], prev_point['longitude'],
                curr_point['latitude'], curr_point['longitude']
            )  # メートル
            
            time_diff = (curr_point['point_time'] - prev_point['point_time']).total_seconds()  # 秒
            
            if time_diff > 0:
                speed_ms = distance / time_diff  # m/s
                speed_kmh = speed_ms * 3.6  # km/h
                trackpoints[i]['speed'] = min(speed_kmh, 200)  # 異常値を制限
            else:
                trackpoints[i]['speed'] = 0
        except:
            trackpoints[i]['speed'] = 0


def calculate_elevation_gain(trackpoints: List[Dict]) -> float:
    """累積標高差を計算"""
    elevation_gain = 0
    prev_elevation = None
    
    for point in trackpoints:
        elevation = point.get('elevation')
        if elevation is not None and prev_elevation is not None:
            if elevation > prev_elevation:
                elevation_gain += elevation - prev_elevation
        prev_elevation = elevation if elevation is not None else prev_elevation
    
    return elevation_gain


def classify_activity(filename: str, track_name: str, trackpoints: List[Dict]) -> str:
    """アクティビティタイプを自動判定（config設定使用）"""
    
    # 設定値の取得
    speed_config = GPX_CONFIG["speed_thresholds"]
    elevation_config = GPX_CONFIG["elevation_thresholds"]
    
    # 1. ファイル名による判定（最優先）
    filename_lower = filename.lower()
    if 'yamap' in filename_lower:
        return 'hiking'
    elif 'run' in filename_lower or 'running' in filename_lower:
        return 'running'
    elif 'bike' in filename_lower or 'cycling' in filename_lower:
        return 'cycling'
    elif 'walk' in filename_lower or 'walking' in filename_lower:
        return 'walking'
    
    # 2. トラック名による判定
    if track_name:
        track_lower = track_name.lower()
        mountain_keywords = ['山', '岳', '峰', '峠', 'mountain', 'peak', 'summit', '登山', 'ハイキング']
        running_keywords = ['run', 'running', 'ラン', 'ランニング', 'ジョギング']
        cycling_keywords = ['bike', 'cycling', 'サイクル', '自転車']
        
        if any(keyword in track_lower for keyword in mountain_keywords):
            return 'hiking'
        elif any(keyword in track_lower for keyword in running_keywords):
            return 'running'
        elif any(keyword in track_lower for keyword in cycling_keywords):
            return 'cycling'
    
    # 3. 移動パターンによる判定（configのしきい値使用）
    if len(trackpoints) > 1:
        # 速度データがある場合
        speeds = [tp.get('speed', 0) for tp in trackpoints if tp.get('speed', 0) > 0]
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
        else:
            avg_speed = 0
        
        # 標高変化の計算
        elevation_gain = calculate_elevation_gain(trackpoints)
        
        # configで定義されたしきい値で判定
        if avg_speed < speed_config["hiking_max"] and elevation_gain > elevation_config["hiking_min_gain"]:
            return 'hiking'
        elif avg_speed < speed_config["walking_max"]:
            return 'walking'
        elif avg_speed < speed_config["running_max"]:
            return 'running'
        elif avg_speed < speed_config["cycling_max"]:
            return 'cycling'
        elif avg_speed >= speed_config["driving_min"]:
            return 'driving'
    
    return 'unknown'


def assign_semantic_type(activity_type: str, track_name: str) -> str:
    """セマンティックタイプを割り当て（config設定使用）"""
    
    # 基本マッピング
    semantic_mapping = {
        'hiking': 'Recreation',
        'running': 'Sports',
        'cycling': 'Sports',
        'walking': 'Recreation',
        'driving': 'Transportation',
        'unknown': 'Other'
    }
    
    # 山岳地帯の特別扱い
    if track_name and any(mountain in track_name for mountain in ['山', '岳', '峰', '高原', '峠']):
        return 'Mountain'
    
    return semantic_mapping.get(activity_type, 'Other')
