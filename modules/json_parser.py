"""
JSON解析モジュール
Android/iPhone形式の判別とデータ構造の解析
"""

from typing import Dict, List, Union, Tuple, Optional
from config import DEBUG


def detect_format(data: Union[Dict, List]) -> str:
    """データ形式を判別する"""
    if isinstance(data, list) and len(data) > 0 and 'startTime' in data[0]:
        return "iphone"
    elif isinstance(data, dict) and 'semanticSegments' in data:
        return "android"
    else:
        raise ValueError("不明なGoogle Timelineデータ形式")


def extract_geo_coordinates(geo_str: str) -> Tuple[Optional[float], Optional[float]]:
    """座標文字列から緯度経度を抽出"""
    if not geo_str or not isinstance(geo_str, str):
        return None, None
    
    try:
        # iPhone形式: "geo:35.639772,139.670222"
        parts = geo_str.replace('geo:', '').split(',')
        if len(parts) >= 2:
            return float(parts[0]), float(parts[1])
    except Exception:
        pass
    
    return None, None


def parse_android_data(data: Dict, username: str) -> List[Dict]:
    """Android形式のデータを解析"""
    records = []
    
    for segment in data['semanticSegments']:
        start_time = segment.get('startTime')
        end_time = segment.get('endTime')
        
        # timelinePath処理
        if 'timelinePath' in segment:
            for path in segment['timelinePath']:
                point_time = path.get('time')
                
                try:
                    lat, lng = map(float, path['point'].replace('°', '').split(', '))
                except Exception:
                    lat, lng = None, None
                
                records.append({
                    "type": "timelinePath",
                    "start_time": start_time,
                    "end_time": end_time,
                    "point_time": point_time,
                    "latitude": lat,
                    "longitude": lng,
                    "visit_probability": None,
                    "visit_placeId": None,
                    "visit_semanticType": None,
                    "activity_distanceMeters": None,
                    "activity_type": None,
                    "activity_probability": None,
                    "username": username
                })
        
        # visit処理
        if 'visit' in segment:
            visit = segment['visit']
            top_candidate = visit.get('topCandidate', {})
            
            try:
                lat, lng = map(float, top_candidate.get('placeLocation', {}).get('latLng', '').replace('°', '').split(', '))
            except Exception:
                lat, lng = None, None
            
            records.append({
                "type": "visit",
                "start_time": start_time,
                "end_time": end_time,
                "point_time": None,
                "latitude": lat,
                "longitude": lng,
                "visit_probability": visit.get('probability'),
                "visit_placeId": top_candidate.get('placeId'),
                "visit_semanticType": top_candidate.get('semanticType'),
                "activity_distanceMeters": None,
                "activity_type": None,
                "activity_probability": None,
                "username": username
            })
        
        # activity処理
        if 'activity' in segment:
            activity = segment['activity']
            top_candidate = activity.get('topCandidate', {})
            
            for key in ['start', 'end']:
                if key in activity and 'latLng' in activity[key]:
                    try:
                        lat, lng = map(float, activity[key]['latLng'].replace('°', '').split(', '))
                    except Exception:
                        lat, lng = None, None
                    
                    records.append({
                        "type": f"activity_{key}",
                        "start_time": start_time,
                        "end_time": end_time,
                        "point_time": None,
                        "latitude": lat,
                        "longitude": lng,
                        "visit_probability": None,
                        "visit_placeId": None,
                        "visit_semanticType": None,
                        "activity_distanceMeters": activity.get('distanceMeters'),
                        "activity_type": top_candidate.get('type'),
                        "activity_probability": top_candidate.get('probability'),
                        "username": username
                    })
    
    return records


def parse_iphone_data(data: List, username: str) -> List[Dict]:
    """iPhone形式のデータを解析"""
    records = []
    
    for segment in data:
        start_time = segment.get('startTime')
        end_time = segment.get('endTime')
        
        # visit処理
        if 'visit' in segment:
            visit = segment['visit']
            top_candidate = visit.get('topCandidate', {})
            place_location = top_candidate.get('placeLocation', '')
            
            lat, lng = extract_geo_coordinates(place_location)
            
            records.append({
                "type": "visit",
                "start_time": start_time,
                "end_time": end_time,
                "point_time": None,
                "latitude": lat,
                "longitude": lng,
                "visit_probability": float(visit.get('probability', 0)) if visit.get('probability') else None,
                "visit_placeId": top_candidate.get('placeID'),
                "visit_semanticType": top_candidate.get('semanticType'),
                "activity_distanceMeters": None,
                "activity_type": None,
                "activity_probability": None,
                "username": username
            })
        
        # activity処理
        if 'activity' in segment:
            activity = segment['activity']
            top_candidate = activity.get('topCandidate', {})
            
            # 開始位置
            start_lat, start_lng = extract_geo_coordinates(activity.get('start', ''))
            if start_lat and start_lng:
                records.append({
                    "type": "activity_start",
                    "start_time": start_time,
                    "end_time": end_time,
                    "point_time": None,
                    "latitude": start_lat,
                    "longitude": start_lng,
                    "visit_probability": None,
                    "visit_placeId": None,
                    "visit_semanticType": None,
                    "activity_distanceMeters": float(activity.get('distanceMeters', 0)) if activity.get('distanceMeters') else None,
                    "activity_type": top_candidate.get('type'),
                    "activity_probability": float(top_candidate.get('probability', 0)) if top_candidate.get('probability') else None,
                    "username": username
                })
            
            # 終了位置
            end_lat, end_lng = extract_geo_coordinates(activity.get('end', ''))
            if end_lat and end_lng:
                records.append({
                    "type": "activity_end",
                    "start_time": start_time,
                    "end_time": end_time,
                    "point_time": None,
                    "latitude": end_lat,
                    "longitude": end_lng,
                    "visit_probability": None,
                    "visit_placeId": None,
                    "visit_semanticType": None,
                    "activity_distanceMeters": float(activity.get('distanceMeters', 0)) if activity.get('distanceMeters') else None,
                    "activity_type": top_candidate.get('type'),
                    "activity_probability": float(top_candidate.get('probability', 0)) if top_candidate.get('probability') else None,
                    "username": username
                })
    
    return records


def parse_json_data(data: Union[Dict, List], username: str) -> List[Dict]:
    """JSONデータを解析してレコードリストを返す"""
    try:
        data_format = detect_format(data)

        if DEBUG:
            print(f"   📱 データ形式: {data_format.upper()}")

        if data_format == "android":
            return parse_android_data(data, username)
        elif data_format == "iphone":
            return parse_iphone_data(data, username)
        else:
            raise ValueError(f"未対応の形式: {data_format}")
            
    except Exception as e:
        if DEBUG:
            print(f"   ❌ データ解析エラー: {e}")
        return []

    return []
