# pokedex
次のデータファイルを作成する
- ポケモン全国図鑑
- ポケモンHOMEのランクマッチ使用率
- ポケモン用語の和名と外国語名の対応表

### ダウンロード
```
git clone https://github.com/tmwork1/pokedex.git
```

### 使い方
全国図鑑の生成
```
python create_zukan.py
```

ランクマッチ使用率の生成
```
python create_battle_data.py
```

言語対応表の生成
```
python create_translation_table.py
```

## 出力形式
JSON形式 : output/json/
CSV形式  : output/csv/

## 引用
ポケモンずかん  
https://zukan.pokemon.co.jp/

ポケモンWiki  
https://wiki.xn--rckteqa2e.com/wiki/%E3%83%A1%E3%82%A4%E3%83%B3%E3%83%9A%E3%83%BC%E3%82%B8

ポケモンHOME (API使用)