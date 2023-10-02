import pandas as pd
import requests
import json
import multiprocessing as mp

def fetch_data(link):
    r = requests.get(link)
    r = json.dumps(r.json())
    loaded_r = json.loads(r)
    print(loaded_r.keys())
    return loaded_r

if __name__ == '__main__':
    new_dict = {}
    new_data = []
    pool = mp.Pool(mp.cpu_count())
    results = []
    df = pd.read_csv('data.csv', encoding='utf-8')
    for i, row in enumerate(df.iterrows()):
        link = f'https://recovery.pr.gov/tpbackend_prod/api/qpr/row-detail/{str(row[1]["TimePeriod"])}/{str(row[1]["DamageId"])}?lang=es'
        results.append(pool.apply_async(fetch_data, args=(link,)))
    pool.close()
    pool.join()
    for i, result in enumerate(results):
        loaded_r = result.get()
        print(i, link)
        for j in loaded_r:
            new_dict['id'] = row[1]['Id']
            new_dict['title'] = loaded_r['title']
            new_dict['diseno'] = loaded_r['flexGroups'][0]['items'][0]['value']
            try:
                new_dict['ncValue'] = loaded_r['flexGroups'][0]['items'][1]['ncValue']
            except Exception as e:
                new_dict['ncValue'] = None
            try:
                new_dict['value1'] = loaded_r['flexGroups'][1]['items'][0]['value']
            except Exception as e:
                new_dict['value1'] = None
            try:
                new_dict['value2'] = loaded_r['flexGroups'][2]['items'][0]['ncValue']
            except Exception as e:
                new_dict['value2'] = None
            try:
                new_dict['value3'] = loaded_r['flexGroups'][2]['items'][1]['ncValue']
            except Exception as e:
                new_dict['value3'] = None
            try:
                new_dict['value4'] = loaded_r['flexGroups'][3]['items'][0]['value']
            except Exception as e:
                new_dict['value4'] = None
            try:
                new_dict['value5'] = loaded_r['flexGroups'][3]['items'][1]['value']
            except Exception as e:
                new_dict['value5'] = None
            try:
                new_dict['value6'] = loaded_r['flexGroups'][4]['items'][0]['value']
            except Exception as e:
                new_dict['value6'] = None
            try:
                new_dict['value7'] = loaded_r['flexGroups'][4]['items'][1]['value']
            except Exception as e:
                new_dict['value7'] = None
            try:
                new_dict['value8'] = loaded_r['flexGroups'][4]['items'][2]['value']
            except Exception as e:
                new_dict['value8'] = None
            try:
                new_dict['value9'] = loaded_r['flexGroups'][4]['items'][3]['value']
            except Exception as e:  
                new_dict['value9'] = None
            try:
                new_dict['value10'] = loaded_r['flexGroups'][5]['items'][0]['value']
            except Exception as e:
                new_dict['value10'] = None
            try:
                new_dict['value11'] = loaded_r['flexGroups'][5]['items'][1]['value']
            except Exception as e:
                new_dict['value11'] = None
            try:
                new_dict['value12'] = loaded_r['flexGroups'][5]['items'][2]['value']
            except Exception as e:
                new_dict['value12'] = None
            try:
                new_dict['value13'] = loaded_r['flexGroups'][5]['items'][3]['value']
            except Exception as e:
                new_dict['value13'] = None
            try:
                new_dict['value14'] = loaded_r['flexGroups'][5]['items'][4]['value']
            except Exception as e:
                new_dict['value14'] = None
            try:
                new_dict['value15'] = loaded_r['flexGroups'][5]['items'][5]['value']
            except Exception as e:
                new_dict['value15'] = None
            try:
                new_dict['value16'] = loaded_r['flexGroups'][5]['items'][6]['value']
            except Exception as e:
                new_dict['value16'] = None
            new_data.append(new_dict.copy())
    new_df = pd.DataFrame(new_data)
    new_df.drop_duplicates(inplace=True)
    new_df.head()
    new_df.to_csv('new_data.csv', index=True, encoding='utf-8')