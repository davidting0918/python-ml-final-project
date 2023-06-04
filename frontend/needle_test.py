import math
from bokeh.plotting import figure, curdoc
from bokeh.models import Label, ColumnDataSource
import random as rd
import pandas as pd

data_path = "db/ml_sentiment_score.csv"
raw_data = pd.read_csv(data_path, index_col=[0]).tail(1)
sentiment_score = raw_data['score'].values[0]

needle_p = figure(width=400, height=400, x_range=(-1.2, 1.2), y_range=(-1.2, 1.2),
                  background_fill_color=None, border_fill_color=None, toolbar_location=None, tools="")
sentiment_score_label = Label(x=0,
                              y=-0.2,
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

needle_p.annular_wedge(x=0, y=0, inner_radius=0.6, outer_radius=1, start_angle=3.14 * 2 / 3, end_angle=3.14,
                       start_angle_units='rad', end_angle_units='rad', fill_color="lightgreen",
                       line_color=None)

needle_p.annular_wedge(x=0, y=0, inner_radius=0.6, outer_radius=1, start_angle=3.14 / 3, end_angle=3.14 * 2 / 3,
                       start_angle_units='rad', end_angle_units='rad', fill_color="yellow",
                       line_color=None)

needle_p.annular_wedge(x=0, y=0, inner_radius=0.6, outer_radius=1, start_angle=0, end_angle=3.14 / 3,
                       start_angle_units='rad', end_angle_units='rad', fill_color="darkred",
                       line_color=None)

pointer_angle = 180 - (180 * (sentiment_score + 1)/2)
pointer_length = 1

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

curdoc().add_root(needle_p)