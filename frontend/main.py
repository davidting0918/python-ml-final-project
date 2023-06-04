"""

"""

# ==========IMPORT PACKAGES===========
import os
from dotenv import load_dotenv

from bokeh.models import Select, Button, Label, DatetimeTickFormatter, Range1d, CDSView, BooleanFilter, HoverTool, ColumnDataSource, NumeralTickFormatter
from bokeh.plotting import curdoc, column, row, figure

import pandas as pd
import numpy as np

from datetime import datetime as dt
from datetime import timedelta as td
import time
import math
import requests as rq

import warnings

from renew_price import get_price, get_symbol
from lib.utility import base64_to_image, create_rgba_from_file

# ==========GLOBAL INITIAL SETTING==========
warnings.filterwarnings("ignore")

# Specify working directory
cfp = os.path.abspath(__file__)
wd = os.path.dirname(cfp)
# os.chdir(wd)

# read .env in frontend
load_dotenv()


# ==========DEFINE FUNCTIONS==========


def update_x_range_callback(attr, old, new):
    global kline_p, price_data, raw_price_data, source
    x_start = kline_p.x_range.start
    x_end = kline_p.x_range.end
    try:
        x_end = x_end.timestamp()
        x_end = dt.fromtimestamp(int(x_end)) - td(hours=8)
    except Exception as e:
        x_end = dt.fromtimestamp(int(x_end) / 1000) - td(hours=8)
    try:
        x_start = x_start.timestamp()
        x_start = dt.fromtimestamp(int(x_start)) - td(hours=8)
    except Exception as e:
        x_start = dt.fromtimestamp(int(x_start) / 1000) - td(hours=8)
    
    # newest_date_in_source_data = pd.DataFrame(source.data)["open_time"].tolist()[0]
    # print(f"Start: {x_start}, End: {x_end}, Newest: {newest_date_in_source_data}")
    
    new_price_data = raw_price_data.loc[(raw_price_data.index > x_start) & (raw_price_data.index < x_end)]
    new_y_range_start = new_price_data["L"].min() * 0.999
    new_y_range_end = new_price_data["H"].max() * 1.001
    
    kline_p.y_range.start = new_y_range_start
    kline_p.y_range.end = new_y_range_end
    kline_p.y_range.reset_start = new_y_range_start
    kline_p.y_range.reset_end = new_y_range_end


def update_token_callback(attr, old, new):
    global source, raw_price_data, price_data, kline_p
    
    new_renderers_list = []
    for i in kline_p.renderers:
        if i.name not in ['segment', 'inc', 'dec']:
            new_renderers_list.append(i)
            continue
    kline_p.renderers = new_renderers_list
    
    file_list = os.listdir(db_path)
    file_name = [i for i in file_list if token_select.value in i][0]
    data_path = f"{db_path}/{file_name}"
    raw_price_data = pd.read_csv(data_path, index_col=[0])
    raw_price_data.index = pd.to_datetime(raw_price_data.index)
    
    new_raw_price_data = raw_price_data.resample(time_select.value).agg({
        'O': 'first',
        'H': 'max',
        'L': 'min',
        'C': 'last',
        'V_Q': 'sum'
    })
    price_data = new_raw_price_data.iloc[x_range_start_index:]
    
    source = ColumnDataSource(data=price_data)
    
    inc = list(price_data.O < price_data.C)
    dec = list(price_data.O > price_data.C)
    inc_cds = CDSView(filters=[BooleanFilter(inc)])
    dec_cds = CDSView(filters=[BooleanFilter(dec)])
    
    kline_p.segment(source=source, x0='open_time', x1='open_time', y0='H', y1='L', color="black", name="segment")
    kline_p.vbar(source=source, view=inc_cds, x='open_time', width=timeunit_width_lookup_table[time_select.value],
                 top='O', bottom='C', fill_color="#D5E1DD",
                 line_color="green", name="inc")
    kline_p.vbar(source=source, view=dec_cds, x='open_time', width=timeunit_width_lookup_table[time_select.value],
                 top='O', bottom='C', fill_color="#F2583E",
                 line_color="red", name='dec')
    
    update_x_range_callback(None, None, None)


def update_time_unit_callback(attr, old, new):
    global price_data, kline_p, source, raw_price_data
    new_renderers_list = []
    for i in kline_p.renderers:
        if i.name not in ['segment', 'inc', 'dec']:
            new_renderers_list.append(i)
            continue
    kline_p.renderers = new_renderers_list
    
    new_raw_price_data = raw_price_data.resample(time_select.value).agg({
        'O': 'first',
        'H': 'max',
        'L': 'min',
        'C': 'last',
        'V_Q': 'sum'
    })
    price_data = new_raw_price_data.iloc[x_range_start_index:]
    
    source = ColumnDataSource(data=price_data)
    
    inc = list(price_data.O < price_data.C)
    dec = list(price_data.O > price_data.C)
    inc_cds = CDSView(filters=[BooleanFilter(inc)])
    dec_cds = CDSView(filters=[BooleanFilter(dec)])
    
    kline_p.segment(source=source, x0='open_time', x1='open_time', y0='H', y1='L', color="black", name="segment")
    kline_p.vbar(source=source, view=inc_cds, x='open_time', width=timeunit_width_lookup_table[time_select.value],
                 top='O', bottom='C', fill_color="#D5E1DD",
                 line_color="green", name="inc")
    kline_p.vbar(source=source, view=dec_cds, x='open_time', width=timeunit_width_lookup_table[time_select.value],
                 top='O', bottom='C', fill_color="#F2583E",
                 line_color="red", name='dec')
    
    new_x_range_start = price_data.iloc[x_range_start_index_cur:].index.tolist()[0] - timedelta_lookup_table[
        time_select.value]
    new_x_range_end = price_data.iloc[x_range_start_index_cur:].index.tolist()[-1] + timedelta_lookup_table[
        time_select.value]
    
    kline_p.x_range.start = new_x_range_start
    kline_p.x_range.end = new_x_range_end
    kline_p.x_range.reset_start = new_x_range_start
    kline_p.x_range.reset_end = new_x_range_end
    
    update_x_range_callback(None, None, None)


def continuous_price_tracker_callback(first=False):
    global kline_p, token_select, source, current_price_label, wd, x_range_start_index_cur
    os.chdir(wd)
    symbol = get_symbol(token=token_select.value)
    start = dt.now() - td(minutes=1)
    end = dt.now()
    temp = get_price(symbol=symbol, start=start, end=end, interval='1s', limit=1)
    current_price = temp.C.values[0]
    source_df = pd.DataFrame(source.data)
    source_df['current_price'] = current_price
    # print(current_price)
    
    start_date = kline_p.x_range.start
    
    if first:
        kline_p.line(x='open_time', y='current_price', color="green", width=1.5, name="current_price",
                     source=ColumnDataSource(source_df))
        current_price_label.x = start_date
        current_price_label.y = current_price
        current_price_label.text = f"{token_select.value}: {current_price}"
        current_price_label.text_color = "green"
        return
    else:
        last_price = float(current_price_label.text.split(":")[-1].strip())
        for index, renderer in enumerate(kline_p.renderers):
            if renderer.name == 'current_price':
                if last_price < current_price:
                    renderer.glyph.line_color = "green"
                    current_price_label.text_color = "green"
                    current_price_label.border_line_color = 'green'
                else:
                    renderer.glyph.line_color = 'red'
                    current_price_label.text_color = "red"
                    current_price_label.border_line_color = 'red'
                renderer.data_source.data = dict(source_df)
                current_price_label.x = start_date
                current_price_label.y = current_price
                current_price_label.text = f"{token_select.value}: {current_price}"


def update_price_and_replot():
    os.chdir(wd)
    os.system("python3 renew_price.py --action update")
    update_token_callback(None, None, None)

# ==========KLINE INITIAL SETTING==========


def create_kline_chart():
    global timedelta_lookup_table, timeunit_width_lookup_table, data_path, db_path, x_range_start_index, \
        x_range_end_index, raw_price_data, price_data, x_range_start_index_cur, x_range_end_index_cur, kline_p, \
        current_price_label, datetime_formatter, token_select, time_select

    # renew price data of each token
    os.chdir(wd)
    os.system("python3 renew_price.py --action update")
    
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
    data_path = os.path.join(wd, 'db/token-price/BTCUSDT.csv')
    db_path = os.path.join(wd, 'db/token-price')

    x_range_start_index = -1000
    x_range_end_index = -1

    raw_price_data = pd.read_csv(data_path, index_col=[0])
    raw_price_data.index = pd.to_datetime(raw_price_data.index)
    price_data = raw_price_data.iloc[x_range_start_index:]

    x_range_start_index_cur = -50
    x_range_end_index_cur = -1
    kline_p = figure(x_axis_type='datetime', title='K-Line Plot', height=500, width=700,
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
    kline_p.yaxis.formatter = NumeralTickFormatter(format='0,0.0000')
    kline_p.grid.grid_line_alpha = 0.3
    
    time_units = ["15min", "30min", "60min", "240min", '1D', '1W', '1M']
    default_time_unit = '15min'
    time_select = Select(title='Time Unit', value=default_time_unit, options=time_units)
    
    token_list = os.getenv("TOKEN_LIST").split(',')
    default_token = 'BTC'
    token_select = Select(title='Token', value=default_token, options=token_list)
    
    time_select.on_change("value", update_time_unit_callback)
    token_select.on_change('value', update_token_callback)
    kline_p.x_range.on_change("start", update_x_range_callback)
    
    # Add tooltips to the plot
    hover_tool = HoverTool(tooltips=[
        ("Date", "@open_time{%Y/%m/%d %H:%M}"),
        ("Open", "@O{0,0.0000}"),
        ("High", "@H{0,0.0000}"),
        ("Low", "@L{0,0.0000}"),
        ("Close", "@C{0,0.0000}"),
        ("Volume", "@V_Q{0.00 a}")
    ], formatters={"@open_time": "datetime"}, )
    kline_p.add_tools(hover_tool)


def create_historical_sentiment_chart():
    global datetime_formatter, historical_sentiment_p, hsp_source
    
    data_path = os.path.join(wd, "db/ml_sentiment_score.csv")
    raw_data = pd.read_csv(data_path, index_col=[0]).astype(float)
    raw_data.index = pd.to_datetime(raw_data.index)
    raw_data['3ma'] = raw_data['score'].rolling(3).mean()
    raw_data['10ma'] = raw_data['score'].rolling(10).mean()
    
    hsp_x_range_start_plot = -30
    hsp_x_range_end_plot = -1
    hsp_source = ColumnDataSource(raw_data)
    
    historical_sentiment_p = figure(width=700, height=500, x_axis_type='datetime',
                                    y_range=Range1d(),
                                    x_range=(
                                    raw_data.index[hsp_x_range_start_plot], raw_data.index[hsp_x_range_end_plot]))
    historical_sentiment_p.line(x='DATE', y='score', width=1.5, color='darkblue', source=hsp_source,
                                name="sentiment score", legend_label='sentiment score')
    historical_sentiment_p.line(x='DATE', y='3ma', width=1.5, color='red', source=hsp_source, alpha=0.6, name="3ma",
                                legend_label='3days moving average')
    historical_sentiment_p.line(x='DATE', y='10ma', width=1.5, color='green', source=hsp_source, alpha=0.6, name="10ma",
                                legend_label='10days moving average')
    
    historical_sentiment_p.xaxis.formatter = datetime_formatter
    historical_sentiment_p.yaxis.formatter = NumeralTickFormatter(format="0.00")
    hover_tool = HoverTool(tooltips=[
        ("Date", "@DATE{%Y/%m/%d}"),
        ("Sentiment Score", "@score{0,0.000}"),
        ("3days moving average", "@3ma{0,0.000}"),
        ("10days moving average", "@10ma{0,0.000}"),
    ], formatters={"@DATE": "datetime"}, )
    historical_sentiment_p.add_tools(hover_tool)
    historical_sentiment_p.legend.location = "bottom_right"
    
    historical_sentiment_p.x_range.on_change("start", update_hsp_range_callback)
    
    
def update_hsp_range_callback(attr, old, new):
    global historical_sentiment_p, hsp_source
    source_df = pd.DataFrame(hsp_source.data).set_index("DATE")
    x_start = historical_sentiment_p.x_range.start
    x_end = historical_sentiment_p.x_range.end
    try:
        x_end = x_end.timestamp()
        x_end = dt.fromtimestamp(int(x_end)) - td(hours=8)
    except Exception as e:
        x_end = dt.fromtimestamp(int(x_end) / 1000) - td(hours=8)
    try:
        x_start = x_start.timestamp()
        x_start = dt.fromtimestamp(int(x_start)) - td(hours=8)
    except Exception as e:
        x_start = dt.fromtimestamp(int(x_start) / 1000) - td(hours=8)
    
    source_df = source_df.loc[(source_df.index > x_start) & (source_df.index < x_end)]
    min_value = source_df[['score', '3ma', '10ma']].min().min()
    max_value = source_df[["score", '3ma', '10ma']].max().max()
    
    new_y_range_start = min_value * 0.1 if min_value > 0 else min_value * 2
    new_y_range_end = max_value * 0.1 if max_value < 0 else max_value * 2
    
    historical_sentiment_p.y_range.start = new_y_range_start
    historical_sentiment_p.y_range.end = new_y_range_end
    historical_sentiment_p.y_range.reset_start = new_y_range_start
    historical_sentiment_p.y_range.reset_end = new_y_range_end
    

def create_needle_chart():
    global needle_p
    data_path = os.path.join(wd, "db/ml_sentiment_score.csv")
    raw_data = pd.read_csv(data_path, index_col=[0]).tail(1)
    sentiment_score = raw_data['score'].values[0]
    inner = 0.6
    outter = 1
    
    needle_p = figure(width=700, height=400, x_range=(-1.5 * outter, 1.5 * outter), y_range=(-1, 3),
                      background_fill_color=None, border_fill_color=None, toolbar_location=None, tools="")
    sentiment_score_label = Label(x=0,
                                  y=-0.3,
                                  name='sentiment_score_label',
                                  text_align='center',
                                  background_fill_alpha=1,
                                  border_line_width=1,
                                  text_font_size='30pt')
    needle_p.add_layout(sentiment_score_label)
    
    needle_p.axis.visible = False
    needle_p.xaxis.visible = False
    needle_p.yaxis.visible = False
    needle_p.xgrid.visible = False
    needle_p.ygrid.visible = False
    needle_p.outline_line_color = None
    
    needle_p.annular_wedge(x=0, y=0, inner_radius=inner, outer_radius=outter, start_angle=3.14 * 2 / 3, end_angle=3.14,
                           start_angle_units='rad', end_angle_units='rad', fill_color="lightgreen",
                           line_color=None)
    
    needle_p.annular_wedge(x=0, y=0, inner_radius=inner, outer_radius=outter, start_angle=3.14 / 3, end_angle=3.14 * 2 / 3,
                           start_angle_units='rad', end_angle_units='rad', fill_color="yellow",
                           line_color=None)
    
    needle_p.annular_wedge(x=0, y=0, inner_radius=inner, outer_radius=outter, start_angle=0, end_angle=3.14 / 3,
                           start_angle_units='rad', end_angle_units='rad', fill_color="darkred",
                           line_color=None)
    
    pointer_angle = 180 - (180 * (sentiment_score + 1) / 2)
    pointer_length = 1.4
    
    pointer_end_x = pointer_length * math.cos(math.radians(pointer_angle))
    pointer_end_y = pointer_length * math.sin(math.radians(pointer_angle))
    
    pointer_x_2 = pointer_length * 0.2 * math.cos(math.radians(pointer_angle + 15))
    pointer_x_3 = pointer_length * 0.2 * math.cos(math.radians(pointer_angle - 15))
    
    pointer_y_2 = pointer_length * 0.2 * math.sin(math.radians(pointer_angle + 15))
    pointer_y_3 = pointer_length * 0.2 * math.sin(math.radians(pointer_angle - 15))
    
    x = [0, pointer_x_2, pointer_end_x, pointer_x_3]
    y = [0, pointer_y_2, pointer_end_y, pointer_y_3]
    
    needle_p.patch(x, y, color='black', alpha=1)
    sentiment_score_label.text = str(round(sentiment_score, 4))
    
    
def create_word_cloud_chart():
    global word_cloud_p
    png_file_path = os.path.join(wd, "db/png/wordcloud.png")
    
    # need to sh start_server.sh in terminal
    """url = "http://127.0.0.1:8000/sentiment"
    b64_string = rq.get(url).json()['word_cloud']
    base64_to_image(b64_string, png_file_path)"""
    
    img, xdim, ydim, dim = create_rgba_from_file(path=png_file_path)
    
    word_cloud_p = figure(width=700, height=400, x_range=(0, 1), y_range=(0, ydim/xdim),
                          background_fill_color=None, border_fill_color=None, toolbar_location=None, tools="")
    word_cloud_p.image_rgba(image=[img], x=0, y=0, dw=1, dh=ydim / xdim, alpha=1, level='overlay', name="word_cloud")
    
    word_cloud_p.axis.visible = False
    word_cloud_p.xaxis.visible = False
    word_cloud_p.yaxis.visible = False
    word_cloud_p.xgrid.visible = False
    word_cloud_p.ygrid.visible = False
    word_cloud_p.outline_line_color = None

# ==========START EXECUTE==========
# Kline chart
create_kline_chart()
update_token_callback(None, None, None)
continuous_price_tracker_callback(first=True)

# historical sentiment chart
create_historical_sentiment_chart()
update_hsp_range_callback(None, None, None)

# create needle
create_needle_chart()

# create word cloud
create_word_cloud_chart()

# Define layout
curdoc().add_periodic_callback(continuous_price_tracker_callback, 1000)
curdoc().add_periodic_callback(update_price_and_replot, 1000*60*15)

layout = row(column(row(word_cloud_p, needle_p), row(time_select, token_select), row(kline_p, historical_sentiment_p)))
curdoc().add_root(layout)