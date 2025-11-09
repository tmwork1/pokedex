import pandas as pd
import re


if __name__ == '__main__':
    with open(f'data/bundle.js', encoding='utf-8') as fin:
        bundle = fin.read()

    # 言語コードを取得
    for s in re.findall(r'langCode:\[(.*?)]', bundle):
        lang = s.replace('"', '').split(',')
        break

    vals = []

    for s in re.findall(r'poke:\[(.*?)]', bundle):
        vals.append(s.replace('"', '').split(','))

    df = pd.DataFrame(vals, index=lang, columns=list(range(1, len(vals[0])+1)))

    # ポケモン名の言語対応表を出力
    dst = f'output/json/name.json'
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(df.to_json(force_ascii=False, indent=4))
    print(dst)

    dst = f'output/csv/name.csv'
    with open(dst, 'w', encoding='utf-8') as f:
        df.T.to_csv(f, lineterminator='\n')
    print(dst)

    tags = ['tokusei', 'waza']
    files = ['ability', 'move']

    # 特性と技の言語対応表を出力
    for tag, file in zip(tags, files):
        vals = []

        for s in re.findall(fr'{tag}:{{(.*?)}}', bundle):
            vals.append(s.split('",'))
            vals[-1] = [v.replace('"', '') for v in vals[-1]]
            vals[-1] = [v[v.index(':')+1:] for v in vals[-1]]

        df = pd.DataFrame(vals, index=lang,
                          columns=list(range(1, len(vals[0])+1)))

        dst = f'output/json/{file}.json'
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(df.to_json(force_ascii=False, indent=4))
        print(dst)

        dst = f'output/csv/{file}.csv'
        with open(dst, 'w', encoding='utf-8') as f:
            df.T.to_csv(f, lineterminator='\n')
        print(dst)
