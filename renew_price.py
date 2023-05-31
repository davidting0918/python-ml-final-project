import os
import requests as rq
from datetime import datetime as dt
import pandas as pd
from dotenv import load_dotenv
load_dotenv()


def get_price(symbol, start, end):
    interval = "15m"
    url = 'https://api.binance.com/api/v3/uiKlines'
    start_timestamp = int(start.timestamp() * 1000)
    end_timestamp = int(end.timestamp() * 1000)
    print(start_timestamp, end_timestamp)
    
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


def get_newest_date(token):
    file_list = os.listdir("db/token-price")
    file_name = [i for i in file_list if token in i][0]
    data_path = f"db/token-price/{file_name}"
    newest_time = pd.to_datetime(pd.read_csv(data_path, index_col=[0]).index).tolist()[-1]
    return newest_time


def get_symbol(token):
    file_list = os.listdir("db/token-price")
    file_name = [i for i in file_list if token in i][0]
    symbol = file_name.split(".")[0]
    return symbol


def to_db(symbol, temp):
    db_path = f"db/token-price/{symbol}.csv"
    token_db = pd.read_csv(db_path, index_col=None)
    token_db = pd.concat([token_db, temp], axis=0)
    token_db.drop_duplicates(inplace=True, subset=['open_time', "close_time"])
    token_db.to_csv(db_path, index=False)
    return len(temp)
    

def main():
    token_list = os.getenv("TOKEN_LIST").split(",")
    
    for token in token_list:
        symbol = get_symbol(token)
        newest_time = get_newest_date(token)
        end = dt.now()
        print(newest_time, end)
        temp = get_price(symbol=symbol, start=newest_time, end=end)
        updated_num = to_db(symbol=symbol, temp=temp)
        print(f"Token:{token} Updated_num:{updated_num}\n\n")


if __name__ == '__main__':
    main()