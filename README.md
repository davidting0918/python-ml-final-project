# python-ml-final-project

## Kline Chart
### 1. kline_chart_template.py
- This code can execute in terminal by `bokeh serve --show kline_chart_templay.py`, please remember to `cd` to **repository directory**.
### 2. renew_price.py
- This code is to renew the price data in the database but need to assign **action** and **token**, can be used by `python3 renew_price.py --action update --token BTC`. Please remember `--action update` is required and if `--token` not specified then will renew **all the tokens** in database.