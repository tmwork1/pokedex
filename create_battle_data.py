from typing import Literal
import requests
import json
import os
import re
import pandas as pd
from copy import deepcopy
from datetime import datetime, timezone, timedelta


def get_current_season(start_year=2022, start_month=12) -> int:
    """現在のシーズン"""
    dt_now = datetime.now(timezone(timedelta(hours=+9), 'JST'))
    y, m, d = dt_now.year, dt_now.month, dt_now.day
    return max(12*(y-start_year) + m - start_month + 1 - (d == 1), 1)


def create_type_code():
    with open(f'data/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'teraType:(.*?)}', fin.read())
        data = ls[0].split(',')
        dict = {}
        for d in data:
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict


def create_nature_code():
    with open(f'data/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'seikaku:(.*?)}', fin.read())
        data = ls[0].split(',')
        dict = {}
        for d in data:
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict


def create_ability_code():
    with open(f'data/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'tokusei:(.*?)}', fin.read())
        data = ls[0].split(',')
        dict = {}
        for d in data:
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict


def create_move_code():
    with open(f'data/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'waza:{(.*?)}', fin.read())
        data = ls[0].split(',')
        dict = {}
        for d in data:
            num = d[:d.index(':')]
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict


def create_item_code():
    with open(f'data/itemname_ja.json', encoding='utf-8') as fin:
        return json.load(fin)['itemname']


def run(platform: Literal["SV", "SwSh"], season_idx, rule_idx):
    print(f"{platform=} {season_idx=}, {rule_idx=}")

    this_dir = os.path.dirname(__file__)

    # 図鑑の読み込み
    with open("output/json/zukan.json", encoding='utf-8') as fin:
        zukan = json.load(fin)

    # デコード表の読み込み
    type_code = create_type_code()
    nature_code = create_nature_code()
    ability_code = create_ability_code()
    move_code = create_move_code()
    item_code = create_item_code()

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'countrycode': '304',
        'authorization': 'Bearer',
        'langcode': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36',
        'content-type': 'application/json',
    }

    # シーズン情報を取得
    if platform == "SV":
        url = 'https://api.battle.pokemon-home.com/tt/cbd/competition/rankmatch/list'
    else:
        url = 'https://api.battle.pokemon-home.com/cbd/competition/rankmatch/list'
    res = requests.post(url, headers=headers, data='{"soft":"Sw"}')
    with open(f'{this_dir}/data/season.json', 'w', encoding='utf-8') as fout:
        fout.write(res.text)
    data = json.loads(res.text)['list']
    current_season = list(data.keys())[season_idx]

    terms = []
    for sn in data:
        for id in data[sn]:
            if data[sn][id]['rule'] == rule_idx:
                terms.append(
                    {'id': id, 'rst': data[sn][id]['rst'], 'ts1': data[sn][id]['ts1'], 'ts2': data[sn][id]['ts2']})

    term = terms[season_idx]
    id, rst, ts1, ts2 = term['id'], term['rst'], term['ts1'], term['ts2']
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36',
        'content-type': 'application/json',
    }

    # ポケモンの使用率を取得
    if platform == "SV":
        url = f'https://resource.pokemon-home.com/battledata/ranking/scvi/{id}/{rst}/{ts2}/pokemon'
    else:
        url = f'https://resource.pokemon-home.com/battledata/ranking/{id}/{rst}/{ts2}/pokemon'

    res = requests.get(url, headers=headers)
    with open(f'{this_dir}/data/pokemon_rank.json', 'w', encoding='utf-8') as fout:
        fout.write(res.text)
    data = json.loads(res.text)
    rank = {}
    for i, d in enumerate(data):
        rank[f"{d['id']:04}-{d['form']:03}"] = i + 1

    # 採用率のランキングを取得
    for x in range(1, 7):
        if platform == "SV":
            url = f'https://resource.pokemon-home.com/battledata/ranking/scvi/{id}/{rst}/{ts2}/pdetail-{x}'
        else:
            url = f'https://resource.pokemon-home.com/battledata/ranking/{id}/{rst}/{ts2}/pdetail-{x}'

        res = requests.get(url, headers=headers)
        with open(f'{this_dir}/data/pokemon_{x}.json', 'w', encoding='utf-8') as fout:
            fout.write(res.text)

    # ポケモンごとに記録されている採用情報を取得する
    # 複数のJSONファイルに分割されている
    adoption = {}
    for x in range(1, 7):
        with open(f'{this_dir}/data/pokemon_{x}.json', encoding='utf-8') as fin:
            data = json.load(fin)

        for id in data:
            for form_id in data[id]:
                key = f"{int(id):04}-{int(form_id):03}"
                if key not in zukan:
                    print(f"\t{key} is not in zukan")
                    continue

                adoption[key] = {'rank': rank[key] if key in rank else 9999}

                for k in ['id', 'form-id', 'name', 'form', 'alias']:
                    adoption[key][k] = zukan[key][k]

                # 技
                for d in data[id][form_id]['temoti']['waza']:
                    name, rate = move_code[str(d['id'])], float(d['val'])
                    adoption[key].setdefault('move', []).append(name)
                    adoption[key].setdefault('move-rate', []).append(rate)

                # 性格
                for d in data[id][form_id]['temoti']['seikaku']:
                    name, rate = nature_code[str(d['id'])], float(d['val'])
                    adoption[key].setdefault('nature', []).append(name)
                    adoption[key].setdefault('nature-rate', []).append(rate)

                # 特性
                for d in data[id][form_id]['temoti']['tokusei']:
                    name, rate = ability_code[str(d['id'])], float(d['val'])
                    adoption[key].setdefault('ability', []).append(name)
                    adoption[key].setdefault('ability-rate', []).append(rate)

                # アイテム
                for d in data[id][form_id]['temoti']['motimono']:
                    name, rate = item_code[str(d['id'])], float(d['val'])
                    adoption[key].setdefault('item', []).append(name)
                    adoption[key].setdefault('item-rate', []).append(rate)

                # テラスタイプ
                for d in data[id][form_id]['temoti']['terastal']:
                    name, rate = type_code[str(d['id'])], float(d['val'])
                    adoption[key].setdefault('terastal', []).append(name)
                    adoption[key].setdefault('terastal-rate', []).append(rate)

    # オーガポンの使用率を修正
    if "1017-000" in adoption:
        # みどりのめん以外
        form_id = 1
        while True:
            key = f"1017-{form_id:03}"
            if key not in zukan:
                break
            adoption[key] = deepcopy(adoption["1017-000"])
            for k in ['id', 'form-id', 'name', 'form', 'alias']:
                adoption[key][k] = zukan[key][k]
            adoption[key]['ability'] = [zukan[key]['ability-1']]
            adoption[key]['ability-rate'] = [100.]
            adoption[key]['item'] = [zukan[key]['form']]
            adoption[key]['item-rate'] = [100.]
            adoption[key]['terastal'] = [zukan[key]['type-2']]
            adoption[key]['terastal-rate'] = [100.0]
            form_id += 1

        # みどりのめん
        key = "1017-000"
        adoption[key]['ability'] = [zukan[key]['ability-1']]
        adoption[key]['terastal'] = [zukan[key]['type-1']]
        items, item_rates = [], []
        for item, rate in zip(adoption[key]['item'], adoption[key]['item-rate']):
            if 'のめん' in item:
                continue
            items.append(item)
            item_rates.append(rate)

        item_rates = [round(100*v/sum(item_rates), 1)
                      for v in item_rates]  # 規格化
        adoption[key]['item'], adoption[key]['item-rate'] = items, item_rates

    # 使用率順に並び替える
    df = pd.DataFrame(adoption).T
    df = df.sort_values(['rank', 'form-id'])

    # 最終出力
    dst = f"{this_dir}/output/json/season{current_season}.json"
    with open(dst, 'w', encoding='utf-8') as fout:
        fout.write(df.T.to_json(force_ascii=False, indent=4))
    print("\t", dst)

    dst = f"{this_dir}/output/csv/season{current_season}.csv"
    with open(dst, 'w', encoding='utf-8') as fout:
        df.to_csv(fout, lineterminator='\n')
    print("\t", dst)


if __name__ == '__main__':
    # 環境
    platform = "SV"

    # ルール（シングル: 0, ダブル: 1）
    rule_idx = 0

    for season_idx in range(get_current_season()):
        run("SV", season_idx, rule_idx)
