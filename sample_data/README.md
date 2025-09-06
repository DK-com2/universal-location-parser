# サンプルデータについて

このディレクトリには、Universal Timeline Parserをテストするためのサンプルデータファイルが含まれています。
これらのファイルには個人情報は含まれておらず、開発・テスト目的のみに使用されるダミーデータです。

## 含まれる主なファイル

- `sample_android.json` - Android 版 Google Timeline サンプル
- `sample_iphone.json` - iPhone 版 Google Timeline サンプル
- `sample_boundary.json` / `sample_boundary.kml` - 緯度経度や時刻の境界値テスト（極値 / 端点 / TimeSpan）
- `dummy_track.kml` / `dummy_track.kmz` - `gx:Track` 動作確認（5 点想定）
- `2024年一級河川_地点ルート.kml` / `2024年一級河川_地点ルート.kmz`  
	- 数千点規模の LineString / Point 展開性能テスト用の大規模サンプル  
	- `.kml` と `.kmz` は内容同一（KMZ 展開ロジックの同値性確認用）

> ヒント: `.kml` と `.kmz` を両方 `data/` に置くとレコードが二重計上されます。通常はどちらか片方で十分です。

## 使用方法

これらのサンプルファイルを使用してパーサーをテストするには：

```bash
# 最小セット（Timeline だけ）
cp sample_data/sample_android.json data/
cp sample_data/sample_iphone.json data/
python main.py

# 統合テスト（JSON + KML/KMZ）
cp sample_data/sample_*.json data/
cp sample_data/dummy_track.kml data/
cp sample_data/sample_boundary.kml data/
python main_unified.py

# 大規模 KML 性能テスト（片方のみ推奨）
cp sample_data/2024年一級河川_地点ルート.kml data/
python main_unified.py
```

### 期待されるレコード数（目安）

| サンプル | 主な type | 想定件数 |
|----------|-----------|----------|
| dummy_track.kml | kml_gx_track | 5 |
| sample_boundary.kml | kml_point / kml_linestring | 7 |
| 2024年一級河川_地点ルート.kml | kml_linestring (+一部 point) | 約 3,132 |
| 2024年一級河川_地点ルート.kmz | 上と同一 | 約 3,132 |

※ 大規模ファイル 2 つを同時に置くと合計 ~6,264 レコードが追加されます。

## 注意事項

- これらはすべてダミー（架空）データで個人情報は含みません。
- 大規模サンプルは性能/メモリ挙動を簡易に測る目的です。ベンチ計測は実行環境差異に注意してください。
- 新形式対応時は 1) 小規模正常系 2) 境界値 3) 大規模ケース の 3 レイヤでサンプルを用意するとレビューが楽になります。
- PR 提出時は、追加サンプルで得られたレコード件数と期待値を CHANGELOG へ記録することを推奨します。

不明点があれば気軽に Issue / Discussion へ投稿してください。学習目的の質問も歓迎です。
