"""

"""

# ==========IMPORT PACKAGES===========
import os
from dotenv import load_dotenv

from bokeh.models import Select, Button, Label, DatetimeTickFormatter, Range1d, CDSView, BooleanFilter, HoverTool
from bokeh.plotting import curdoc, column, row, figure

import pandas as pd
import numpy as np

from datetime import datetime as dt
from datetime import timedelta as td
import time

import warnings

from renew_price import get_price, get_symbol

# ==========GLOBALINITIAL SETTING==========
warnings.filterwarnings("ignore")

# Specify working directory
cfp = os.path.abspath(__file__)
wd = os.path.dirname(cfp)
os.chdir(wd)

# read .env in frontend
load_dotenv()


# ==========KLINE INITIAL SETTING==========
# renew price data of each token
# os.system("python3 renew_price.py --action update")

timedelta_lookup_table = {
    "15min": td(minutes=15),
    "30min": td(minutes=30),
    "60min": td(minutes=60),
    "240min": td(hours=4),
    "1D": td(days=1),
    "1W": td(weeks=1),
    "1M": td(days=30)
}

timeunit_width_lookup_table = {
    "15min": td(minutes=15*2/3),
    "30min": td(minutes=30*2/3),
    "60min": td(minutes=60*2/3),
    "240min": td(hours=4*2/3),
    "1D": td(days=1*2/3),
    "1W": td(days=7*2/3),
    "1M": td(days=30*2/3)
}
data_path = 'db/token-price/BTCUSDT.csv'
db_path = 'db/token-price'

x_range_start_index = -1000
x_range_end_index = -1

raw_price_data = pd.read_csv(data_path, index_col=[0])
raw_price_data.index = pd.to_datetime(raw_price_data.index)
price_data = raw_price_data.iloc[x_range_start_index:]

x_range_start_index_cur = -50
x_range_end_index_cur = -1
kline_p = figure(x_axis_type='datetime', title='K-Line Plot', height=500, width=900,
                 x_range=(price_data.index[x_range_start_index_cur], price_data.index[x_range_end_index_cur]),
                 y_range=Range1d())
current_price_label = Label(name='current_price_label',
                            background_fill_color='lightgray',
                            background_fill_alpha=1,
                            border_line_width=1,
                            text_font_size='15pt')
kline_p.add_layout(current_price_label)
datetime_formatter = DatetimeTickFormatter(
    days=["%Y/%m/%d"],
    months=["%Y/%m/%d"],
    hours=["%Y/%m/%d %H:%M"],
    minutes=["%Y/%m/%d %H:%M"]
)

kline_p.xaxis.formatter = datetime_formatter
kline_p.grid.grid_line_alpha = 0.3
