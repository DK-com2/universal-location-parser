import io
import zipfile
from pathlib import Path
from modules.kml_parser import parse_kml_file


def _write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def test_kmz_without_dockml(tmp_path: Path):
    # KMZ 内に doc.kml が無く、alt.kml のみ存在するケース
    kmz_path = tmp_path / "no_doc_kml.kmz"
    kml_content = """
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
      <Document>
        <Placemark>
          <Point><coordinates>139.7,35.6,10</coordinates></Point>
          <TimeStamp><when>2025-01-01T00:00:00Z</when></TimeStamp>
        </Placemark>
      </Document>
    </kml>
    """.strip()
    with zipfile.ZipFile(kmz_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("alt.kml", kml_content)
    recs = parse_kml_file(str(kmz_path))
    assert len(recs) == 1
    assert recs[0]["type"].startswith("kml_")
    assert recs[0]["point_time"] == "2025-01-01T00:00:00Z"


def test_timespan_linestring(tmp_path: Path):
    # TimeSpan を持つ LineString の各頂点が展開される
    kml_path = tmp_path / "timespan.kml"
    kml_content = """
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <Placemark>
          <TimeSpan>
            <begin>2025-02-01T00:00:00Z</begin>
            <end>2025-02-01T01:00:00Z</end>
          </TimeSpan>
          <LineString>
            <coordinates>
              139.7,35.6,10 139.8,35.7,20
            </coordinates>
          </LineString>
        </Placemark>
      </Document>
    </kml>
    """.strip()
    _write_text(kml_path, kml_content)
    recs = parse_kml_file(str(kml_path))
    assert len(recs) == 2
    for r in recs:
        assert r["start_time"] == "2025-02-01T00:00:00Z"
        assert r["end_time"] == "2025-02-01T01:00:00Z"


def test_gx_track_mismatch_pairs(tmp_path: Path):
    # when と coord の数が不一致でも短い方に合わせて抽出
    kml_path = tmp_path / "gx_mismatch.kml"
    kml_content = """
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
      <Document>
        <Placemark>
          <gx:Track>
            <when>2025-03-01T00:00:00Z</when>
            <when>2025-03-01T00:10:00Z</when>
            <gx:coord>139.70 35.60 10</gx:coord>
          </gx:Track>
        </Placemark>
      </Document>
    </kml>
    """.strip()
    _write_text(kml_path, kml_content)
    recs = parse_kml_file(str(kml_path))
    assert len(recs) == 1
    assert recs[0]["point_time"] == "2025-03-01T00:00:00Z"


def test_deep_nested_features(tmp_path: Path):
    # 深い入れ子の Placemark でも座標が抽出される
    kml_path = tmp_path / "nested.kml"
    kml_content = """
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <Folder>
          <Folder>
            <Placemark>
              <Point><coordinates>139.9,35.9,5</coordinates></Point>
            </Placemark>
          </Folder>
        </Folder>
      </Document>
    </kml>
    """.strip()
    _write_text(kml_path, kml_content)
    recs = parse_kml_file(str(kml_path))
    assert len(recs) == 1
    assert recs[0]["latitude"] == 35.9
    assert recs[0]["longitude"] == 139.9


def test_gx_multitrack(tmp_path: Path):
    # gx:MultiTrack 配下の gx:Track を抽出
    kml_path = tmp_path / "multitrack.kml"
    kml_content = """
    <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
      <Document>
        <Placemark>
          <gx:MultiTrack>
            <gx:Track>
              <when>2025-04-01T00:00:00Z</when>
              <gx:coord>139.70 35.60 10</gx:coord>
            </gx:Track>
            <gx:Track>
              <when>2025-04-01T00:05:00Z</when>
              <gx:coord>139.71 35.61 11</gx:coord>
            </gx:Track>
          </gx:MultiTrack>
        </Placemark>
      </Document>
    </kml>
    """.strip()
    _write_text(kml_path, kml_content)
    recs = parse_kml_file(str(kml_path))
    assert len(recs) == 2
    times = sorted(r["point_time"] for r in recs)
    assert times == ["2025-04-01T00:00:00Z", "2025-04-01T00:05:00Z"]
