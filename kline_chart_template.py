import numpy as np
import pandas as pd
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, RangeTool, DatetimeTickFormatter, CDSView, BooleanFilter, Range1d, Label
from bokeh.layouts import column, row
from bokeh.models import Select, HoverTool
from datetime import datetime as dt
from datetime import timedelta as td
from bokeh.layouts import gridplot
import os
from dotenv import load_dotenv
import warnings
from renew_price import get_price, get_symbol
warnings.filterwarnings("ignore")
load_dotenv()

os.system("python3 renew_price.py --action update")
# os.system("python3 price_cleaner.py")

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

# Create the Bokeh figure
kline_p = figure(x_axis_type='datetime', title='K-Line Plot', height=800, width=1500,
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

time_units = ["15min", "30min", "60min", "240min", '1D', '1W', '1M']
default_time_unit = '15min'
time_select = Select(title='Time Unit', value=default_time_unit, options=time_units)

token_list = os.getenv("TOKEN_LIST").split(',')
default_token = 'BTC'
token_select = Select(title='Token', value=default_token, options=token_list)


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
    
    newest_date_in_source_data = pd.DataFrame(source.data)["open_time"].tolist()[0]
    print(f"Start: {x_start}, End: {x_end}, Newest: {newest_date_in_source_data}")
    
    new_price_data = raw_price_data.loc[(raw_price_data.index > x_start) & (raw_price_data.index < x_end)]
    new_y_range_start = new_price_data["L"].min() * 0.999
    new_y_range_end = new_price_data["H"].max() * 1.001
    
    kline_p.y_range.start = new_y_range_start
    kline_p.y_range.end = new_y_range_end
    kline_p.y_range.reset_start = new_y_range_start
    kline_p.y_range.reset_end = new_y_range_end
    
    if (newest_date_in_source_data - x_start) < timedelta_lookup_table[time_select.value]:
        return

    """new_price_data_plot = raw_price_data.loc[:pd.to_datetime(newest_date_in_source_data)].tail(abs(x_range_start_index))
    new_source = ColumnDataSource(data=new_price_data_plot)

    inc = list(new_price_data_plot.O < new_price_data_plot.C)
    dec = list(new_price_data_plot.O > new_price_data_plot.C)
    inc_cds = CDSView(filters=[BooleanFilter(inc)])
    dec_cds = CDSView(filters=[BooleanFilter(dec)])

    p.segment(source=new_source, x0='open_time', x1='open_time', y0='H', y1='L', color="black", name="segment")
    p.vbar(source=new_source, view=inc_cds, x='open_time', width=td(minutes=10), top='O', bottom='C',
           fill_color="#D5E1DD",
           line_color="green", name="inc")
    p.vbar(source=new_source, view=dec_cds, x='open_time', width=td(minutes=10), top='O', bottom='C',
           fill_color="#F2583E",
           line_color="red", name='dec')
    source = ColumnDataSource(new_price_data)"""


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
    kline_p.vbar(source=source, view=inc_cds, x='open_time', width=timeunit_width_lookup_table[time_select.value], top='O', bottom='C', fill_color="#D5E1DD",
                 line_color="green", name="inc")
    kline_p.vbar(source=source, view=dec_cds, x='open_time', width=timeunit_width_lookup_table[time_select.value], top='O', bottom='C', fill_color="#F2583E",
                 line_color="red", name='dec')

    new_y_range_start = price_data.iloc[x_range_start_index_cur:]["L"].min() * 0.995
    new_y_range_end = price_data.iloc[x_range_start_index_cur:]["H"].max() * 1.001
    
    new_x_range_start = price_data.iloc[x_range_start_index_cur:].index.tolist()[0] - timedelta_lookup_table[time_select.value]
    new_x_range_end = price_data.iloc[x_range_start_index_cur:].index.tolist()[-1] + timedelta_lookup_table[time_select.value]
    
    kline_p.y_range.start = new_y_range_start
    kline_p.y_range.end = new_y_range_end
    kline_p.y_range.reset_start = new_y_range_start
    kline_p.y_range.reset_end = new_y_range_end

    kline_p.x_range.start = new_x_range_start
    kline_p.x_range.end = new_x_range_end
    kline_p.x_range.reset_start = new_x_range_start
    kline_p.x_range.reset_end = new_x_range_end


def update_token_callback(attr, old, new):
    """Need to update time unit"""
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
    kline_p.vbar(source=source, view=inc_cds, x='open_time', width=timeunit_width_lookup_table[time_select.value], top='O', bottom='C', fill_color="#D5E1DD",
                 line_color="green", name="inc")
    kline_p.vbar(source=source, view=dec_cds, x='open_time', width=timeunit_width_lookup_table[time_select.value], top='O', bottom='C', fill_color="#F2583E",
                 line_color="red", name='dec')

    new_y_range_start = price_data.iloc[x_range_start_index_cur: x_range_end_index_cur]["L"].min() * 0.995
    new_y_range_end = price_data.iloc[x_range_start_index_cur: x_range_end_index_cur]["H"].max() * 1.001
    
    kline_p.y_range.start = new_y_range_start
    kline_p.y_range.end = new_y_range_end
    kline_p.y_range.reset_start = new_y_range_start
    kline_p.y_range.reset_end = new_y_range_end
    
    
def continuous_price_tracker_callback(first=False):
    global kline_p, token_select, source, current_price_label
    symbol = get_symbol(token=token_select.value)
    start = dt.now() - td(minutes=1)
    end = dt.now()
    temp = get_price(symbol=symbol, start=start, end=end, interval='1s', limit=1)
    current_price = temp.C.values[0]
    source_df = pd.DataFrame(source.data)
    source_df['current_price'] = current_price
    print(current_price)
    
    label_index = -9
    if first:
        kline_p.line(x='open_time', y='current_price', color="green", width=3, name="current_price", source=ColumnDataSource(source_df))
        current_price_label.x = source_df['open_time'].values[label_index]
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
                current_price_label.x = source_df['open_time'].values[label_index]
                current_price_label.y = current_price
                current_price_label.text = f"{token_select.value}: {current_price}"


time_select.on_change("value", update_time_unit_callback)
token_select.on_change('value', update_token_callback)
kline_p.x_range.on_change("start", update_x_range_callback)

# Add tooltips to the plot
hover_tool = HoverTool(tooltips=[
    ("Date", "@open_time{%Y/%m/%d %H:%M}"),
    ("Open", "@O{0,0.4f}"),
    ("High", "@H{0,0.4f}"),
    ("Low", "@L{0,0.4f}"),
    ("Close", "@C{0,0.4f}"),
    ("Volume", "@V_Q{0.00 a}")
], formatters={"@open_time": "datetime"}, )
kline_p.add_tools(hover_tool)

# Create the layout and add it to the current document
layout = column(row(time_select, token_select), kline_p)

update_token_callback(None, None, None)
continuous_price_tracker_callback(first=True)

curdoc().add_periodic_callback(continuous_price_tracker_callback, 2000)
curdoc().add_root(layout)
