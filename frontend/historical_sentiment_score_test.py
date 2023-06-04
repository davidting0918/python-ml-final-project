from bokeh.plotting import curdoc, column, row, figure
from bokeh.models import ColumnDataSource, Label, Button, Range1d, HoverTool, Legend, DatetimeTickFormatter, NumeralTickFormatter
from datetime import datetime as dt
from datetime import timedelta as td
import pandas as pd
import os

cfp = os.path.abspath(__file__)
wd = os.path.dirname(cfp)
os.chdir(wd)

data_path = "db/ml_sentiment_score.csv"
raw_data = pd.read_csv(data_path, index_col=[0]).astype(float)
raw_data.index = pd.to_datetime(raw_data.index)
raw_data['3ma'] = raw_data['score'].rolling(3).mean()
raw_data['10ma'] = raw_data['score'].rolling(10).mean()

hsp_x_range_start_plot = -10
hsp_x_range_end_plot = -1
hsp_source = ColumnDataSource(raw_data)

historical_sentiment_p = figure(width=900, height=500, x_axis_type='datetime',
                                y_range=Range1d(),
                                x_range=(raw_data.index[hsp_x_range_start_plot], raw_data.index[hsp_x_range_end_plot]))
historical_sentiment_p.line(x='DATE', y='score', width=1.5, color='darkblue', source=hsp_source,
                            name="sentiment score", legend_label='sentiment score')
historical_sentiment_p.line(x='DATE', y='3ma', width=1.5, color='red', source=hsp_source, alpha=0.6, name="3ma",
                            legend_label='3days moving average')
historical_sentiment_p.line(x='DATE', y='10ma', width=1.5, color='green', source=hsp_source, alpha=0.6, name="10ma",
                            legend_label='10days moving average')
datetime_formatter = DatetimeTickFormatter(
    days=["%Y/%m/%d"],
    months=["%Y/%m/%d"],
    hours=["%Y/%m/%d %H:%M"],
    minutes=["%Y/%m/%d %H:%M"]
)

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


update_hsp_range_callback(None, None, None)
historical_sentiment_p.x_range.on_change("start", update_hsp_range_callback)

curdoc().add_root(historical_sentiment_p)