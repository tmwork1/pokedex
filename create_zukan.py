from alias import *
import json
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import mojimoji


# zkn_form_ja.jsonに含まれないフォルム
additional_forms = {
    'コオリッポ': ['アイスフェイス', 'ナイスフェイス'],
    'イルカマン': ['ナイーブフォルム', 'マイティフォルム'],
    'シャリタツ': ['そったすがた', 'たれたすがた', 'のびたすがた'],
    'オーガポン': ['みどりのめん', 'いどのめん', 'かまどのめん', 'いしずえのめん'],
}

# 公式図鑑にない情報
forms = ['ちいさいサイズ', 'ふつうのサイズ', 'おおきいサイズ', 'とくだいサイズ']
bakeccha_weight = {form: v for form, v in zip(forms, [3.5, 5, 7.5, 15])}
bakeccha_height = {form: v for form, v in zip(forms, [0.3, 0.4, 0.5, 0.8])}
panpujin_weight = {form: v for form, v in zip(forms, [9.5, 12.5, 14, 39])}
panpujin_height = {form: v for form, v in zip(forms, [0.7, 0.9, 1.1, 1.7])}

# 古い世代から順
wiki_urls = [
    'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%B8%80%E4%B8%96%E4%BB%A3)',
    '',
    'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%B8%89%E4%B8%96%E4%BB%A3)',
    'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E5%9B%9B%E4%B8%96%E4%BB%A3)',
    'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%BA%94%E4%B8%96%E4%BB%A3)',
    'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E5%85%AD%E4%B8%96%E4%BB%A3)',
    'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%B8%83%E4%B8%96%E4%BB%A3)',
    'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E5%85%AB%E4%B8%96%E4%BB%A3)',
    'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%B9%9D%E4%B8%96%E4%BB%A3)',
]

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.google.com/",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


def create_zukan_from_HOME() -> dict:
    """
    ポケモンHOMEの内部データを解析して図鑑データを作成する
    """
    # ポケモンの名前を読み込む
    with open(f'data/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'poke:\[(.*?)\]', fin.read())
        names = ls[0].split(',')
        names = [s[1:-1] for s in names]  # ""を除去

    # フォルム情報を読み込む
    with open(f'data/zkn_form_ja.json', encoding='utf-8') as fin:
        dict = json.load(fin)
        forms = {}
        for key in dict['zkn_form'].keys():
            if not key[:3].isdigit() or len(key) > 8:
                continue
            d = key.index('_')
            id = str(int(key[:d]))
            form_id = str(int(key[d+1:d+4]))
            if id not in forms:
                forms[id] = {}
            forms[id][form_id] = dict['zkn_form'][key]

    # 登録されていないフォルムを追加
    for name in additional_forms:
        id = names.index(name) + 1
        forms[str(id)] = {}
        for form_id, form in enumerate(additional_forms[name]):
            forms[str(id)][str(form_id)] = form

    # 図鑑の辞書に格納する
    # key = "図鑑番号(4桁)-フォルム番号(3桁)"
    zukan = {}

    for i, name in enumerate(names):
        id = i + 1

        key = f"{id:04}-{0:03}"
        zukan[key] = {}
        aliases = []

        if str(id) not in forms or '0' not in forms[str(id)]:
            zukan[key]['id'] = id
            zukan[key]['form-id'] = 0
            zukan[key]['name'] = name
            zukan[key]['form'] = ''
            zukan[key]['alias'] = alias(zukan[key])
            aliases.append(zukan[key]['alias'])

        # フォルム違いがある場合
        if str(id) in forms:
            for form_id in forms[str(id)]:
                key = f"{id:04}-{int(form_id):03}"
                dict = {}
                dict['id'] = id
                dict['form-id'] = int(form_id)
                dict['name'] = name
                dict['form'] = forms[str(id)][form_id]
                dict['alias'] = alias(dict)

                # aliasが重複していればスキップ
                if (s := dict['alias']) in aliases:
                    print(f"Duplicated alias : {s}")
                    continue

                zukan[key] = dict
                aliases.append(dict['alias'])

    return zukan


def update_zukan_with_official_dex(zukan: dict):
    """
    公式の図鑑サイトから情報を取得して図鑑データに追記する
    """
    # 公式図鑑で使われているタイプコードを読み込む
    with open(f'data/zukan_type.json', encoding='utf-8') as fin:
        zukan_types = [''] + list(json.load(fin).keys())

    # 公式の図鑑サイトから情報を取得
    prev_id, prev_form_id = 0, 0

    for key in zukan:
        data = zukan[key]

        # 初期化
        data['category'] = ''
        data['weight'] = 0
        data['height'] = 0
        for k in ['type-1', 'type-2']:
            data[k] = ''
        for k in ['ability-1', 'ability-2', 'ability-3']:
            data[k] = ''

        url = f"https://zukan.pokemon.co.jp/detail/{data['id']:04}"

        # フォルムに基づいてURLを修正
        if (fid := data['form-id']) > 0:
            if data['id'] == prev_id and fid != prev_form_id + 1:
                fid = prev_form_id + 1
            url += f"-{fid}"

        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            s = soup.find(id='json-data').get_text()
        except:
            print(f"Failed to access zukan {data['alias']} : {url}")
            continue

        json_text = s[s.index('{'):s.rindex('}')+1]
        json_data = json.loads(json_text)

        data['category'] = json_data['pokemon']['bunrui']
        data['weight'] = json_data['pokemon']['omosa']
        data['height'] = json_data['pokemon']['takasa']
        for k in ['type-1', 'type-2']:
            data[k] = zukan_types[json_data['pokemon'][k.replace("-", "_")]]
        for i, abilities in enumerate(json_data['abilities']):
            data[f"ability-{i+1}"] = abilities['name']

        # 手動で情報を追加
        if data['name'] == 'バケッチャ':
            data['weight'] = bakeccha_weight[data['form']]
            data['height'] = bakeccha_height[data['form']]
        elif data['name'] == 'パンプジン':
            data['weight'] = panpujin_weight[data['form']]
            data['height'] = panpujin_height[data['form']]

        prev_id, prev_form_id = data['id'], fid

        print(f"公式図鑑から追記 {list(data.values())}")


def update_zukan_with_wiki(zukan):
    """
    ポケモンWikiから、特性と種族値を取得して図鑑データに追記する
    """

    # 特性の取得
    url = "https://wiki.xn--rckteqa2e.com/wiki/%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%81%AE%E3%81%A8%E3%81%8F%E3%81%9B%E3%81%84%E4%B8%80%E8%A6%A7"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table')

    form_abbr = {
        'A': 'アローラのすがた',
        'G': 'ガラルのすがた',
        'H': 'ヒスイのすがた',
        'P': 'パルデアのすがた',
    }

    for i, tr in enumerate(table.find_all('tr')):
        if i == 0:
            continue

        data = [td.text.strip() for td in tr.find_all('td')]
        # print(data)

        # 名前とフォルムを取得
        name, form = data[1], ''

        if '(' in name:
            name = data[1][:data[1].index('(')]
            form = data[1][data[1].index('(')+1:-1]

        if name[-1] in ['A', 'G', 'H', 'P']:
            form = form_abbr[name[-1]]
            name = name[:-1]

        for mark, s in zip(['♂', '♀'], ['オスのすがた', 'メスのすがた']):
            if name[-1] == mark and 'ニドラン' not in name:
                name = name[:-1]
                form = s

        name = mojimoji.han_to_zen(name)
        form = mojimoji.han_to_zen(form)

        if name in ['カラナクシ', 'トリトドン', 'シキジカ', 'メブキジカ']:
            form = ''

        # 図鑑に追加
        for key, d in zukan.items():
            matched = d['name'] == name
            if form:
                matched &= d['form'] == form

            if matched:
                abilities = [
                    zukan[key][f"ability-{j+1}"] for j in range(3) if zukan[key][f"ability-{j+1}"]]
                for ability in data[2:5]:
                    if len(abilities) == 3:
                        break
                    if not ability:
                        continue

                    for s in ['*', '[']:
                        if s in ability:
                            ability = ability[:ability.index(s)]
                    if ability not in abilities:
                        zukan[key][f"ability-{len(abilities)+1}"] = ability
                        print(f"\tAdded {ability} to", zukan[key]['alias'])

    stat_labels = ['H', 'A', 'B', 'C', 'D', 'S']

    # 種族値などの取得

    # 初期化
    for key in zukan:
        # 最後に登場した世代
        zukan[key]['last_gen'] = 0
        # 種族値
        for s in stat_labels:
            zukan[key][s] = 0

    zukan_names = [d['name'] for d in zukan.values()]

    for g, url in enumerate(wiki_urls):
        if not url:
            continue

        print(f"{g+1}th generation", url)

        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')

        for i, tr in enumerate(table.find_all('tr')):
            if i == 0:
                continue

            data = [td.text.strip() for td in tr.find_all(['th', 'td'])]
            # print(data)

            # 名前とフォルムの修正
            name, form = data[1], ''

            if '(' in name:
                name = data[1][:data[1].index('(')]
                form = data[1][data[1].index('(')+1:-1]

            if '・' in form:
                form = form[:form.index('・')]

            for mark, s in zip(['♂', '♀'], ['オスのすがた', 'メスのすがた']):
                if name[-1] == mark and 'ニドラン' not in name:
                    name = name[:-1]
                    form = s

            if name == 'メテノ' and 'コア' in form:
                form = 'あかいろのコア'

            if name == 'フーパ':
                form = form.replace('すがた', 'フーパ')

            if len(name) > 6:
                for n in range(3, 7):
                    if name[:n] in zukan_names:
                        form = name[n:]
                        name = name[:n]
                        break

            name = mojimoji.han_to_zen(name)
            form = mojimoji.han_to_zen(form)

            # 図鑑に追加
            for key, d in zukan.items():
                matched = d['name'] == name
                if form:
                    matched &= d['form'] == form

                if matched:
                    # 最後に登場した世代を記録
                    if f"メガ{d['name']}" in d['form']:
                        zukan[key]['last_gen'] = 7
                    elif "キョダイ" in d['form']:
                        zukan[key]['last_gen'] = 8
                    else:
                        zukan[key]['last_gen'] = g + 1

                    # 種族値を記録
                    for j, v in enumerate(data[4:10]):
                        zukan[key][stat_labels[j]] = int(v)


def dump(zukan):
    # json出力
    with open(f'output/json/zukan.json', 'w', encoding='utf-8') as fout:
        json.dump(zukan, fout, ensure_ascii=False, indent=4)

    # csv出力
    with open(f'output/csv/zukan.csv', 'w', encoding='utf-8') as fout:
        df = pd.DataFrame(zukan)
        df.T.to_csv(fout, lineterminator='\n')


def load_zukan() -> dict:
    with open(f'output/json/zukan.json', encoding='utf-8') as fin:
        return json.load(fin)


if __name__ == '__main__':
    # 1) ポケモンHOMEの内部データからデータ取得
    zukan = create_zukan_from_HOME()

    # 2) 公式の図鑑サイトからデータ取得 [かなり時間がかかる]
    update_zukan_with_official_dex(zukan)

    # 3) ポケモンWikiからデータ取得 [すこし時間がかかる]
    update_zukan_with_wiki(zukan)

    # 最終出力
    dump(zukan)
