"""
KML/KMZ 解析モジュール
=========================
Google Earth などでエクスポートされる **KML / KMZ** ファイルから、タイムスタンプ付き
位置情報（緯度・経度・標高）を抽出し、汎用的な dict リスト形式で返します。

既存の ``gpx_parser.py`` や ``json_parser.py`` と同じスキーマを維持することで、
``main_unified.py`` 側に大きな改修を入れずそのまま統合できます。

主要機能
---------
* **gx:Track** ― Google 拡張タグを優先解析（<when> + <gx:coord>）
* **Placemark (Point / LineString / MultiGeometry)** ― fastkml で抽出
* **KMZ** ― ZIP 展開して ``doc.kml`` を自動読込（なければ最初の .kml を採用）
* **エラー耐性** ― 破損ファイル・未知ジオメトリを警告ログに残しスキップ

依存
----
* fastkml >= 1.0.0
* lxml >= 4.9

使い方例
--------
>>> from kml_parser import parse_kml_file
>>> recs = parse_kml_file("data/track.kmz", username="alice")
>>> print(recs[0])
{'latitude': 35.681, 'longitude': 139.767, 'elevation': 25.3,
 'point_time': '2025-07-01T09:00:15Z', 'type': 'kml_gx_track',
 'username': 'alice'}

"""
from __future__ import annotations

import logging
import os
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from fastkml import kml as _kml  # type: ignore
from lxml import etree  # nosec B410

_LOGGER = logging.getLogger(__name__)
# KML標準・Google拡張の名前空間定義
_NS = {
    "kml": "http://www.opengis.net/kml/2.2",
    "gx": "http://www.google.com/kml/ext/2.2",
}

__all__ = [
    "parse_kml_file",
]

# ---------------------------------------------------------------------------
# 内部ヘルパー関数群
# ---------------------------------------------------------------------------

def _read_kml_bytes(filepath: str | os.PathLike) -> bytes:
    """
    KMLまたはKMZファイルからKMLバイト列を取得する。
    KMZの場合はZIP展開してdoc.kmlを抽出。なければ最初に見つかった.kmlを使用。
    Args:
        filepath (str | Path): KMLまたはKMZファイルのパス。
    Returns:
        bytes: KMLファイルのバイト列。
    Raises:
        FileNotFoundError: ファイルが存在しない、またはKMZ内にKMLが見つからない場合。
    """
    path = Path(filepath)
    if path.suffix.lower() == ".kmz":
        with zipfile.ZipFile(path, "r") as kmz:
            try:
                return kmz.read("doc.kml")
            except KeyError:
                # doc.kml がない場合、最初の .kml を探す
                candidates = [n for n in kmz.namelist() if n.lower().endswith(".kml")]
                if candidates:
                    # doc.kml に近い名前を優先
                    candidates.sort(key=lambda n: ("doc.kml" not in n.lower(), len(n)))
                    chosen = candidates[0]
                    _LOGGER.debug("KMZ内の代替KMLを使用: %s", chosen)
                    return kmz.read(chosen)
                raise FileNotFoundError("KMZ 内に KML ファイルが見つかりません")
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_bytes()


def _extract_gx_track(root: etree._Element) -> List[Dict]:  # noqa: WPS110
    """
    <gx:Track>要素から時刻・座標を抽出し、dictリスト化（Google拡張対応）。
    Args:
        root (etree._Element): KMLのルート要素。
    Returns:
        List[Dict]: 各track点のdictリスト。
    Note:
        - <when>と<gx:coord>の数が不一致の場合は短い方に合わせる。
        - 座標パース失敗時はスキップ。
        - MultiTrack配下のTrackも .//gx:Track で拾われる。
    """
    records: List[Dict] = []
    for track in root.findall(".//gx:Track", namespaces=_NS):
        whens = [e.text for e in track.findall("kml:when", namespaces=_NS)]
        coords = [e.text for e in track.findall("gx:coord", namespaces=_NS)]
        if len(whens) != len(coords):
            _LOGGER.warning("gx:Track の when と coord の数が不一致: %s vs %s", len(whens), len(coords))
        for when, coord in zip(whens, coords):  # zipで短い方に合わせる
            try:
                lon, lat, *ele = map(float, coord.split())
            except ValueError:  # pragma: no cover
                _LOGGER.debug("無効な座標文字列: %s", coord)
                continue
            records.append(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "elevation": ele[0] if ele else None,
                    "point_time": when,
                    "type": "kml_gx_track",
                },
            )
    return records


def _extract_simple_geometries(k: _kml.KML) -> List[Dict]:  # noqa: WPS231
    """
    Placemark配下のPoint/LineString/MultiGeometryを再帰的に抽出。
    Args:
        k (_kml.KML): fastkmlでパース済みKMLオブジェクト。
    Returns:
        List[Dict]: 各ジオメトリ点のdictリスト。
    Note:
        - MultiGeometryは再帰的にflatten。
        - geometryが空の場合はスキップ。
    """
    records: List[Dict] = []

    def _walk(feat):  # noqa: WPS430
        # featuresが関数かリストかを判定して適切に処理
        if hasattr(feat, "features"):
            try:
                # 関数として呼び出してみる
                features = feat.features()
            except TypeError:
                # リストの場合
                features = feat.features
            
            for f in features:
                if hasattr(f, "geometry") and f.geometry is not None:
                    _handle_geometry(f.geometry, records)
                if hasattr(f, "features"):
                    _walk(f)

    def _handle_geometry(geom, store: List[Dict]):  # noqa: WPS231
        """
        ジオメトリをflattenし座標列をdict化して追加。
        Args:
            geom: fastkmlのgeometryオブジェクト。
            store (List[Dict]): 結果格納リスト。
        """
        geom_type = geom.__class__.__name__.lower()
        if getattr(geom, "is_empty", False):  # type: ignore[attr-defined]
            return
        try:
            coords_iter = list(geom.coords)  # type: ignore[attr-defined]
        except AttributeError:
            # MultiGeometryの場合は再帰的に処理
            if hasattr(geom, "geoms"):
                for sub in geom.geoms:  # type: ignore[attr-defined]
                    _handle_geometry(sub, store)
            return
        for lon, lat, *rest in coords_iter:
            store.append(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "elevation": rest[0] if rest else None,
                    "type": f"kml_{geom_type}",
                },
            )

    _walk(k)
    return records


def _parse_coordinates_text(text: Optional[str]) -> List[tuple]:
    """KMLの<coordinates>文字列を (lon, lat, ele?) のリストに解析。"""
    if not text:
        return []
    items: List[tuple] = []
    for token in text.replace("\n", " ").replace("\t", " ").split():
        parts = token.split(",")
        try:
            lon = float(parts[0])
            lat = float(parts[1]) if len(parts) > 1 else None
            ele = float(parts[2]) if len(parts) > 2 else None
            if lat is not None:
                items.append((lon, lat, ele))
        except Exception:  # pragma: no cover - 不正トークンはスキップ
            continue
    return items


def _extract_placemark_with_times(root: etree._Element) -> List[Dict]:
    """TimeStamp/TimeSpan を持つ Placemark の座標を抽出し時間を付与。"""
    recs: List[Dict] = []
    for pm in root.findall(".//kml:Placemark", namespaces=_NS):
        # 時刻の抽出
        ts = pm.find("kml:TimeStamp/kml:when", namespaces=_NS)
        tspan_begin = pm.find("kml:TimeSpan/kml:begin", namespaces=_NS)
        tspan_end = pm.find("kml:TimeSpan/kml:end", namespaces=_NS)
        point_time = ts.text if ts is not None else None
        start_time = tspan_begin.text if tspan_begin is not None else None
        end_time = tspan_end.text if tspan_end is not None else None
        if not any([point_time, start_time, end_time]):
            continue
        # Point
        for coords in pm.findall(".//kml:Point/kml:coordinates", namespaces=_NS):
            for lon, lat, ele in _parse_coordinates_text(coords.text):
                recs.append(
                    {
                        "latitude": lat,
                        "longitude": lon,
                        "elevation": ele,
                        "point_time": point_time,
                        "start_time": start_time,
                        "end_time": end_time,
                        "type": "kml_point",
                    }
                )
        # LineString（各頂点を点として展開）
        for coords in pm.findall(".//kml:LineString/kml:coordinates", namespaces=_NS):
            for lon, lat, ele in _parse_coordinates_text(coords.text):
                recs.append(
                    {
                        "latitude": lat,
                        "longitude": lon,
                        "elevation": ele,
                        "point_time": point_time,
                        "start_time": start_time,
                        "end_time": end_time,
                        "type": "kml_linestring",
                    }
                )
    return recs


def _extract_geometries_without_times(root: etree._Element) -> List[Dict]:
    """Time要素が無いPlacemarkの Point/LineString をlxmlで直接抽出。"""
    recs: List[Dict] = []
    # Point
    for coords in root.findall(".//kml:Placemark//kml:Point/kml:coordinates", namespaces=_NS):
        for lon, lat, ele in _parse_coordinates_text(coords.text):
            recs.append(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "elevation": ele,
                    "point_time": None,
                    "start_time": None,
                    "end_time": None,
                    "type": "kml_point",
                }
            )
    # LineString → 各頂点
    for coords in root.findall(".//kml:Placemark//kml:LineString/kml:coordinates", namespaces=_NS):
        for lon, lat, ele in _parse_coordinates_text(coords.text):
            recs.append(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "elevation": ele,
                    "point_time": None,
                    "start_time": None,
                    "end_time": None,
                    "type": "kml_linestring",
                }
            )
    return recs

# ---------------------------------------------------------------------------
# Public API（外部公開関数）
# ---------------------------------------------------------------------------

def parse_kml_file(filepath: str | os.PathLike, *, username: str | None = None) -> List[Dict]:
    """
    指定したKML/KMZファイルをパースし、位置情報dictのリストを返す。
    Args:
        filepath (str | Path): KML/KMZファイルのパス。
        username (str | None): 各レコードに付与するユーザー名（任意）。
    Returns:
        List[Dict]: 位置情報dictリスト（スキーマはdocstring参照）。
    Note:
        - gx:Track（Google拡張）があれば優先。
        - TimeStamp/TimeSpan付きPlacemarkを次に試行。
        - それでもなければPlacemark配下のPoint/LineString等を抽出。
        - username指定時は全レコードに付与。
    """
    kml_bytes = _read_kml_bytes(filepath)

    # --- gx:Track (Google 拡張) 優先 ---
    root = etree.fromstring(kml_bytes)  # nosec B314
    records = _extract_gx_track(root)

    # --- 次に TimeStamp/TimeSpan 付き Placemark ---
    if not records:
        timed = _extract_placemark_with_times(root)
        if timed:
            records = timed

    # --- fallback: Placemark (Point/LineString etc.) ---
    if not records:
        k = _kml.KML()
        k.from_string(kml_bytes)
        records = _extract_simple_geometries(k)

    # --- 最終fallback: lxmlでの幾何抽出（shapely未導入環境向け） ---
    if not records:
        records = _extract_geometries_without_times(root)

    # usernameを付与（指定時）
    if username is not None:
        for rec in records:
            rec["username"] = username
    else:
        for rec in records:
            rec.setdefault("username", None)

    return records

# ---------------------------------------------------------------------------
# CLIエントリポイント（オプション）
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Parse KML/KMZ file and dump JSON")
    parser.add_argument("filepath", help="path to .kml/.kmz file")
    parser.add_argument("--username", help="username to annotate", default=None)
    parser.add_argument("-o", "--output", help="output json path (default: stdout)")
    args = parser.parse_args()

    result = parse_kml_file(args.filepath, username=args.username)
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
