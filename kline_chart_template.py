import numpy as np
import pandas as pd
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, RangeTool, DatetimeTickFormatter, CDSView, BooleanFilter, Range1d
from bokeh.layouts import column, row
from bokeh.models import Select, HoverTool
from datetime import datetime as dt
from datetime import timedelta as td
from bokeh.layouts import gridplot
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")
load_dotenv()

timedelta_lookup_table = {
    "15min": td(minutes=15),
    "30min": td(minutes=30),
    "60min": td(minutes=60),
    "240min": td(hours=4),
    "1D": td(days=1),
    "1W": td(weeks=1),
    "1M": td(days=30),
    "3M": td(days=92),
    "1Y": td(days=365)
}

data_path = 'db/token-price/BTCUSDT.csv'
db_path = 'db/token-price'

x_range_start_index = -2000
x_range_end_index = -1

raw_price_data = pd.read_csv(data_path, index_col=[0])
raw_price_data.index = pd.to_datetime(raw_price_data.index)
price_data = raw_price_data.iloc[x_range_start_index:]

source = ColumnDataSource(data=price_data)

inc = list(price_data.O < price_data.C)
dec = list(price_data.O > price_data.C)
inc_cds = CDSView(filters=[BooleanFilter(inc)])
dec_cds = CDSView(filters=[BooleanFilter(dec)])

x_range_start_index_cur = -50
x_range_end_index_cur = -1

# Create the Bokeh figure
p = figure(x_axis_type='datetime', title='K-Line Plot', height=800, width=1500, x_range=(price_data.index[x_range_start_index_cur], price_data.index[x_range_end_index_cur]))
datetime_formatter = DatetimeTickFormatter(
    days=["%m/%d %H:%M"],
    months=["%m/%d %H:%M"],
    hours=["%m/%d %H:%M"],
    minutes=["%m/%d %H:%M"])

p.xaxis.formatter = datetime_formatter
p.grid.grid_line_alpha = 0.3

p.y_range = Range1d(price_data.iloc[x_range_start_index_cur: x_range_end_index_cur]["L"].min() * 0.995,
                    price_data.iloc[x_range_start_index_cur: x_range_end_index_cur]["H"].max() * 1.001)

p.segment(source=source, x0='open_time', x1='open_time', y0='H', y1='L', color="black", name="segment")
p.vbar(source=source, view=inc_cds, x='open_time', width=td(minutes=10), top='O', bottom='C', fill_color="#D5E1DD", line_color="green", name="inc")
p.vbar(source=source, view=dec_cds, x='open_time', width=td(minutes=10), top='O', bottom='C', fill_color="#F2583E", line_color="red", name='dec')

time_units = ["15min", "30min", "60min", "240min", '1D', '1W', '1M', '3M', '1Y']
default_time_unit = '15min'
time_select = Select(title='Time Unit', value=default_time_unit, options=time_units)

token_list = os.getenv("TOKEN_LIST").split(',')
default_token = 'BTC'
token_select = Select(title='Token', value=default_token, options=token_list)


def update_x_range_callback(attr, old, new):
    global p, price_data, raw_price_data, source
    x_start = p.x_range.start
    x_end = 0 if pd.isna(p.x_range.end) else p.x_range.end
    if x_end == 0:
        return
    # The date from bokeh is another GMT+8
    x_start = dt.fromtimestamp(x_start / 1000) - td(hours=8)
    x_end = dt.fromtimestamp(x_end / 1000) - td(hours=8)
    
    newest_date_in_source_data = pd.DataFrame(source.data)["open_time"].tolist()[0]
    
    if (newest_date_in_source_data - x_start) < timedelta_lookup_table[time_select.value]:
        return
    
    new_price_data = raw_price_data.loc[(raw_price_data.index > x_start) & (raw_price_data.index < x_end)]
    diff = list(set(new_price_data.index.tolist()) - set(price_data.index.tolist()))
    
    new_price_data_plot = new_price_data.loc[new_price_data.index.isin(diff)]
    
    new_source = ColumnDataSource(data=new_price_data_plot)

    inc = list(new_price_data_plot.O < new_price_data_plot.C)
    dec = list(new_price_data_plot.O > new_price_data_plot.C)
    inc_cds = CDSView(filters=[BooleanFilter(inc)])
    dec_cds = CDSView(filters=[BooleanFilter(dec)])
    
    p.segment(source=new_source, x0='open_time', x1='open_time', y0='H', y1='L', color="black", name="segment")
    p.vbar(source=new_source, view=inc_cds, x='open_time', width=td(minutes=10), top='O', bottom='C', fill_color="#D5E1DD",
           line_color="green", name="inc")
    p.vbar(source=new_source, view=dec_cds, x='open_time', width=td(minutes=10), top='O', bottom='C', fill_color="#F2583E",
           line_color="red", name='dec')
    
    source = ColumnDataSource(new_price_data)


def update_time_unit_callback(attr, old, new):
    global price_data
    new_price_data = raw_price_data.resample(time_select.value).agg({
        'O': 'first',
        'H': 'max',
        'L': 'min',
        'C': 'last',
        'V_Q': 'sum'
    })
    print(new_price_data)
    

def update_token_callback(attr, old, new):
    global source, raw_price_data, price_data, p
    
    new_renderers_list = []
    for i in p.renderers:
        if i.name not in ['segment', 'inc', 'dec']:
            new_renderers_list.append(i)
            continue
    p.renderers = new_renderers_list

    file_list = os.listdir(db_path)
    file_name = [i for i in file_list if token_select.value in i][0]
    data_path = f"{db_path}/{file_name}"
    raw_price_data = pd.read_csv(data_path, index_col=[0])
    raw_price_data.index = pd.to_datetime(raw_price_data.index)
    
    source_data_start = pd.to_datetime(pd.DataFrame(source.data)['open_time']).tolist()[0]
    source_data_end = pd.to_datetime(pd.DataFrame(source.data)['open_time']).tolist()[-1]
    price_data = raw_price_data.loc[source_data_start:source_data_end]

    source = ColumnDataSource(data=price_data)
    
    p.segment(source=source, x0='open_time', x1='open_time', y0='H', y1='L', color="black", name="segment")
    p.vbar(source=source, view=inc_cds, x='open_time', width=td(minutes=10), top='O', bottom='C', fill_color="#D5E1DD",
           line_color="green", name="inc")
    p.vbar(source=source, view=dec_cds, x='open_time', width=td(minutes=10), top='O', bottom='C', fill_color="#F2583E",
           line_color="red", name='dec')

    new_y_range_start = price_data.iloc[x_range_start_index_cur: x_range_end_index_cur]["L"].min() * 0.995
    new_y_range_end = price_data.iloc[x_range_start_index_cur: x_range_end_index_cur]["H"].max() * 1.001
    
    p.y_range.start = new_y_range_start
    p.y_range.end = new_y_range_end
    p.y_range.reset_start = new_y_range_start
    p.y_range.reset_end = new_y_range_end
    
time_select.on_change("value", update_time_unit_callback)
token_select.on_change('value', update_token_callback)
# p.x_range.on_change("start", update_x_range_callback)

# Add tooltips to the plot
hover_tool = HoverTool(tooltips=[
    ("Date", "@open_time{%m/%d %H:%M}"),
    ("Open", "@O{0,0.4f}"),
    ("High", "@H{0,0.4f}"),
    ("Low", "@L{0,0.4f}"),
    ("Close", "@C{0,0.4f}"),
    ("Volume", "@V_Q{0.00 a}")
], formatters={"@open_time": "datetime"}, )
p.add_tools(hover_tool)

# Create the layout and add it to the current document
layout = column(row(time_select, token_select), p)

curdoc().add_root(layout)
