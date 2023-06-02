import os
import requests as rq
from datetime import datetime as dt
from datetime import timedelta as td
import pandas as pd
from dotenv import load_dotenv
import argparse as arg
load_dotenv()


def get_price(symbol, start, end):
    interval = "15m"
    url = 'https://api.binance.com/api/v3/uiKlines'
    start_timestamp = int(start.timestamp() * 1000)
    end_timestamp = int(end.timestamp() * 1000)
    
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': 1000,
        'startTime': start_timestamp,
        "endTime": end_timestamp
    }
    data = rq.get(url, params=params).json()
    
    columns = ["open_time", "O", "H", "L", "C", "V_C", "close_time", "V_Q"]
    
    temp = pd.DataFrame([i[:8] for i in data], columns=columns)
    temp['open_time'] = [dt.fromtimestamp(i / 1000) for i in temp['open_time'].tolist()]
    temp['close_time'] = [dt.fromtimestamp(i / 1000) for i in temp['close_time'].tolist()]
    temp.loc[:, ["O", "H", "L", "C", "V_C", "V_Q"]] = temp.loc[:, ["O", "H", "L", "C", "V_C", "V_Q"]].astype(float)
    temp = temp.loc[:, ["open_time", "close_time", "O", "H", "L", "C", "V_Q", "V_C"]]
    return temp


def fill_missing_interval(token):
    file_list = os.listdir("db/token-price")
    file_name = [i for i in file_list if token in i][0]
    data_path = f"db/token-price/{file_name}"
    
    db = pd.read_csv(data_path, index_col=[0])
    db.index = pd.to_datetime(db.index)
    db_date_list = db.index.tolist()
    
    missing = 0
    for index, date in enumerate(db_date_list):
        
        if index == len(db_date_list) - 1:
            continue
        if (db_date_list[index + 1] - date) != td(minutes=15):
            start = date
            end = db_date_list[index + 1]
            
            symbol = get_symbol(token=token)
            temp = get_price(symbol=symbol, start=start, end=end)
            updated_num = to_db(symbol=symbol, temp=temp)
            print(f"Token:{token} Time: {start} Fill_num:{updated_num} \n")
            missing += 1
            
    return missing
    
    
def get_newest_date_in_db(token):
    file_list = os.listdir("db/token-price")
    file_name = [i for i in file_list if token in i][0]
    data_path = f"db/token-price/{file_name}"
    newest_time = pd.to_datetime(pd.read_csv(data_path, index_col=None)['close_time']).tolist()[-1] - td(hours=8)
    return newest_time


def get_symbol(token):
    file_list = os.listdir("db/token-price")
    file_name = [i for i in file_list if token in i][0]
    symbol = file_name.split(".")[0]
    return symbol


def to_db(symbol, temp):
    db_path = f"db/token-price/{symbol}.csv"
    token_db = pd.read_csv(db_path, index_col=None)
    
    old_db_len = len(token_db)
    token_db = pd.concat([token_db, temp], axis=0)
    token_db = token_db.drop_duplicates(subset=['open_time', "close_time"])
    new_db_len = len(token_db)
    
    token_db['open_time'] = pd.to_datetime(token_db['open_time'])
    token_db.sort_values(by='open_time', ascending=True, inplace=True)
    
    token_db.to_csv(db_path, index=False)
    
    return new_db_len - old_db_len
    

def main():
    token_list = os.getenv("TOKEN_LIST").split(",")
    parser = arg.ArgumentParser()
    parser.add_argument('--token')
    parser.add_argument("--action")
    
    args = parser.parse_args()
    
    if args.token is None and args.action == "update":
        for token in token_list:
            symbol = get_symbol(token)
            newest_time = get_newest_date_in_db(token)
            end = dt.now()
            temp = get_price(symbol=symbol, start=newest_time, end=end)
            updated_num = to_db(symbol=symbol, temp=temp)
            print(f"Token:{token} Updated_num:{updated_num}")
    
    if args.token is None and args.action == "fill":
        pass
    
    if args.action == "fill":
        token = args.token
        fill_missing_num = fill_missing_interval(token=token)
        print(f"===========\n"
              f"Token: {token} Fill_num: {fill_missing_num}"
              f"===========\n")


if __name__ == '__main__':
    main()