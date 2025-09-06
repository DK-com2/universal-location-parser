from pathlib import Path
from modules.kml_parser import parse_kml_file

FIXTURE = Path(__file__).parent.parent / "sample_data" / "dummy_track.kml"

def test_dummy_kml_gxtrack():
    recs = parse_kml_file(FIXTURE)
    assert len(recs) == 5                 # gx:Track で 5 点（サンプルに合わせる）
    assert recs[0]["type"] == "kml_gx_track"
