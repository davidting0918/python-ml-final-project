# ========IMPORT PACKAGES============
import pandas as pd
import requests as rq
from dotenv import load_dotenv
from datetime import datetime as dt
from datetime import timedelta as td
from tqdm import tqdm
from lib.Tools import TG
TG = TG()

import argparse as arg
import os
import time


# ========DEFINE FUNCTION============
def get_symbol_price(symbol, start, end, interval):
    if interval == "1m":
        return
    
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

def get_symbol_listing_time(symbol):
    url = 'https://api.binance.com/api/v3/uiKlines'
    start_timestamp = int(dt(year=2000, month=1, day=1, hour=0, minute=0, second=0).timestamp() * 1000)
    
    params = {
        'symbol': symbol,
        'interval': "1d",
        'limit': 1,
        'startTime': start_timestamp,
    }
    data = rq.get(url, params=params).json()
    
    try:
        listing_date = dt.fromtimestamp(data[0][0] / 1000)
        return listing_date
    
    except Exception as e:
        return dt.today()
    

def to_db(token, symbol, date, temp):
    # to token specific all db, remember to drop duplicated date.
    # make sure there is sub-folder in the db, if not create one.
    folder_path = f"db/{token}"
    subfolder_path = f"db/{token}/sub"
    
    db_path = f"{folder_path}/{symbol}.csv"
    date_db_path = f"{subfolder_path}/{symbol}_{date.strftime('%Y%m%d')}.csv"
    
    if os.path.exists(folder_path):
        # get all database
        token_all_db = pd.read_csv(db_path, index_col=None)
        token_all_db = pd.concat([token_all_db, temp], axis=0)
        token_all_db.drop_duplicates(inplace=True, subset=['open_time', "close_time"])
        token_all_db.to_csv(db_path, index=False)
    
        # to date db
        # temp.to_csv(date_db_path, index=False)
        return True
    
    else:
        os.mkdir(folder_path)
        # os.mkdir(subfolder_path)
        temp.to_csv(db_path, index=False)
        # temp.to_csv(date_db_path, index=False)
    
    
def process_token(token, listing_symbol, start_date, end_date, args):
    david_chat_id = os.getenv("DAVID_TG_CHAT_ID")
    bot_api = os.getenv("ALERT_BOT_API_KEY")
    
    
    days = (end_date - start_date).days
    for i in tqdm(range(days), unit='days', desc="Processing......."):
        start = start_date + td(days=i)
        end = start_date + td(days=i + 1)
        temp = get_symbol_price(symbol=listing_symbol, start=start, end=end, interval=args.interval)
        to_db(token=token, symbol=listing_symbol, date=start, temp=temp)
        # print(f"{start} -- {listing_symbol}")
        time.sleep(0.5)

def main():
    parser = arg.ArgumentParser()
    parser.add_argument('--token')
    parser.add_argument('--start')
    parser.add_argument('--end')
    parser.add_argument('--interval')
    args = parser.parse_args()

    # =========READ ENVIRONMENT VARIABLE======
    load_dotenv()
    token_list = os.getenv("TOKEN_LIST").split(",")
    

    if args.token is None:  # if not specify token, then renew all
        for token in token_list:
            listing_date, listing_symbol = min(
                (get_symbol_listing_time(symbol), symbol) for symbol in [f"{token}USDT", f"{token}USDC"]
            )
        
            start_date = listing_date if args.start is None else dt.strptime(args.start, "%Y%m%d")
            end_date = dt.today() if args.end is None else dt.strptime(args.end, "%Y%m%d")
        
            process_token(token, listing_symbol, start_date, end_date, args)
            time.sleep(10)
    else:
        token = args.token
        listing_date, listing_symbol = min(
            (get_symbol_listing_time(symbol), symbol) for symbol in [f"{token}USDT", f"{token}USDC"]
        )
    
        start_date = listing_date if args.start is None else dt.strptime(args.start, "%Y%m%d")
        end_date = dt.today() if args.end is None else dt.strptime(args.end, "%Y%m%d")
    
        process_token(token, listing_symbol, start_date, end_date, args)


if __name__ == "__main__":
    main()