# ====================================================================================
# Author:David Ding
# Date:2022/11/18
# Purpose:This file contains little tools for formatter and send message in TG
#
# ====================================================================================

# =========IMPORT PACKAGES=========
from decimal import Decimal
from beautifultable import BeautifulTable
import requests as rq
import numpy as np
import prettytable as pt


# =========DEFINE CLASS=========
class Formatter():
    def __int__(self):
        pass

    def millify(self, n, k: int = 3):
        def remove_exponent(num):
            return num.to_integral() if num == num.to_integral() else num.normalize()

        import math
        millnames = ['', 'K', 'M', 'B', 'T']
        n = float(n)
        millidx = max(0, min(len(millnames) - 1,
                             int(math.floor(0 if n == 0 else math.log10(abs(n)) / 3))))

        simplified_num = n / 10 ** (3 * millidx)
        digit = max(k - (len(str(simplified_num).split(".")[0])), 0)

        simplified_num = remove_exponent(Decimal(str(round(simplified_num, digit))))

        return f"{simplified_num}{millnames[millidx]}"

    def get_progress(self, current, total, digit=2):
        perc = round(((current+1) / total) * 100, digit)
        filled_blocks = int(perc // 10)
        empty_blocks = 10 - filled_blocks
        progress_bar = "[" + "■" * filled_blocks + "□" * empty_blocks + "]"

        return perc, progress_bar

    def create_text_lst(self, df, data_type):
        text_lst = []
        df_len = len(df)

        if df_len == 0:
            text_lst.append(" ")
            return text_lst
        else:
            times = (df_len // 20) + 1
            if df_len % 20 == 0:
                times -= 1
            start = 0
            end = min(20, df_len)

            for i in range(times):
                end = min(df_len, end)
                table_text = self.create_bt_from_df(df=df, start=start, end=end, this_page=i + 1, all_page=times,
                                                    data_type=data_type)
                text_lst.append(table_text)
                start += 20
                end += 20

            return text_lst

    def create_bt_from_df(self, df, start, end, this_page, all_page, data_type):
        table = BeautifulTable()
        if data_type == "top":
            for index, row in df.iloc[start:end].iterrows():
                table.rows.append(
                    [index,
                     self.millify(row[0]),
                     f"{self.millify(row[1] * 100)}%",
                     self.millify(round(row[2]))])

        elif data_type == "new":
            for index, row in df.iloc[start:end].iterrows():
                table.rows.append(
                    [index,
                     self.millify(row[0]),
                     "-" if row[1] == np.infty else f"{self.millify(row[1]*100)}%",
                     self.millify(round(row[2]))])

        table.columns.header = df.reset_index().columns.to_list()

        for i in range(len(df.columns)):
            if i == 0:
                table.columns.alignment[df.columns[i]] = BeautifulTable.ALIGN_LEFT
            else:
                table.columns.alignment[df.columns[i]] = BeautifulTable.ALIGN_RIGHT

        table.set_style(BeautifulTable.STYLE_BOX)

        data_width = 22 // len(df.columns)
        table.columns.width = [8] + [data_width] * len(df.columns)

        table_text = f"<pre>{table}</pre>"
        return table_text

    def create_pretty_table(self, df, data_type):
        if data_type == "top":
            columns = df.reset_index().columns.to_list()

            table = pt.PrettyTable(columns)
            for index, row in df.iterrows():
                table.add_row([index,
                              self.millify(row[0]),
                              f"{format(round(row[1]*100), ',')}%",
                              self.millify(round(row[2]))]
                              )

            for column in columns:
                if column == columns[0]:
                    table.align[column] = 'l'

                else:
                    table.align[column] = "r"

        elif data_type == "new":
            columns = df.reset_index().columns.to_list()

            table = pt.PrettyTable(columns)
            for index, row in df.iterrows():
                table.add_row([index,
                               self.millify(row[0]),
                               "-" if row[1] == np.infty else f"{format(round(row[1]*100), ',')}%",
                               self.millify(round(row[2]))]
                              )

            for column in columns:
                if column == columns[0]:
                    table.align[column] = 'l'

                else:
                    table.align[column] = "r"

        print(table)
        return table


class TG():
    def __int__(self):
        pass

    def message_send(self, bot_api, chat_id, text="default", parse_mode="HTML"):
        url = f"https://api.telegram.org/bot{bot_api}/sendMessage?chat_id={chat_id}&" \
              f"text={text}&parse_mode={parse_mode}"

        res = rq.get(url).json()['result']
        return res

    def message_edit(self, bot_api, chat_id, message_id, text, parse_mode="HTML"):
        # URL for editing the message text
        url = f"https://api.telegram.org/bot{bot_api}/editMessageText"

        # Parameters for the API request
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }

        res = rq.post(url, json=params).json()['result']
        return res