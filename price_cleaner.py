from dotenv import load_dotenv
import pandas as pd
import os
load_dotenv()


def main():
    token_list = os.getenv("TOKEN_LIST").split(",")
    
    for token in token_list:
        file_list = os.listdir("db/token-price")
        file_name = [i for i in file_list if token in i][0]
        data_path = f"db/token-price/{file_name}"
        db = pd.read_csv(data_path, index_col=None)
        
        old_db_len = len(db)
        db.drop_duplicates(subset=['open_time', 'close_time'], inplace=True, keep="last")
        new_db_len = len(db)
        
        db.to_csv(data_path, index=False)
        print(token, old_db_len, new_db_len)
        


if __name__ == '__main__':
    main()