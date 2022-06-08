"""Script for comparing cryptocurrency charts from different sources."""
import json
import datetime

import pandas as pd
import plotly.express as px
import plotly.utils
import requests

from flask import (Blueprint, render_template, request, flash)

exchanges_urls = {
    'KuCoin': 'https://api.kucoin.com',
    'Binance': 'https://api.binance.com',
    'FTX': 'https://ftx.com/api'
}
klines_urls = {
    'KuCoin': '/api/v1/market/candles',
    'Binance': '/api/v3/klines',
    'FTX': '/markets/{market_name}/candles'
}
ex_pair_separator = {
    'KuCoin': '-',
    'Binance': '',
    'FTX': '/'
}
ex_interval_phrase = {
    'KuCoin': 'type',
    'Binance': 'interval',
    'FTX': 'resolution'
}
ex_time_phrase = {
    'start': {
        'KuCoin': 'startAt',
        'Binance': 'startTime',
        'FTX': 'start_time'
    },
    'end': {
        'KuCoin': 'endAt',
        'Binance': 'endTime',
        'FTX': 'end_time'
    }
}
ex_timeframes = {
    'KuCoin': '1day',
    'Binance': '1d',
    'FTX': '86400'
}
ex_factor = {
    'KuCoin': 1,
    'Binance': 1000,
    'FTX': 1
}

bp = Blueprint('coins', __name__)


def get_exchanges_list(ex):
    """Return a list of available exchanges"""
    return [ex for ex in ex.keys()]

def get_symbol(coin1, coin2, ex):
    """Return currency pair symbol."""
    return ex_pair_separator.get(ex).join((coin1.upper(), coin2.upper()))

def get_market(s, symbol):
    if '{' in s and '}' in s:
        return s.format(market_name=symbol) + '?'
    return f'{s}?symbol={symbol}&'

def get_data_url(coin1, coin2, ex, tf, start_time=datetime.datetime.now()-datetime.timedelta(days=60), end_time=datetime.datetime.now(), symbol=None) :
    """"Return the URL to an endpoint with data from the exchange."""
    symbol = get_symbol(coin1, coin2, ex)
    start_time = str(int(float(datetime.datetime.timestamp(start_time)) * ex_factor.get(ex)))
    end_time = str(int(float(datetime.datetime.timestamp(end_time)) * ex_factor.get(ex)))
    url_string = f"{exchanges_urls.get(ex)}{get_market(klines_urls.get(ex), symbol)}{ex_interval_phrase.get(ex)}={tf}&"\
            f"{ex_time_phrase.get('start')[ex]}={start_time}&{ex_time_phrase.get('end')[ex]}={end_time}"
    return url_string

def get_kucoin_data(data):
    """Return statistics data and data chart from kucoin exchange."""
    if data.get('code') == '200000':
        if len(data.get('data')) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.fromtimestamp(int(t[0])-1)+datetime.timedelta(days=1) for t in data.get('data')],
                'Cena zamknięcia': [float(p[2]) for p in data.get('data')],
                'Giełda': ['KuCoin' for i in range(len(data.get('data')))]
            })
            return df
        return 'Brak danych dla tego okresu.'
    return data

def get_binance_data(data):
    """Return statistics data and data chart from binance exchange."""
    if type(data) == list:
        if len(data) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.fromtimestamp(float(t[6])/1000) for t in data],
                'Cena zamknięcia': [float(p[4]) for p in data],
                'Giełda': ['Binance' for i in range(len(data))]
            })
            return df
        return 'Brak danych dla tego okresu.'
    return data

def get_ftx_data(data):
    if data.get('success') is True:
        if len(data.get('result')) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.strptime(t.get('startTime'), '%Y-%m-%dT%H:%M:%S%z') +
                         datetime.timedelta(hours=2, seconds=int(ex_timeframes.get('FTX'))) for t in data.get('result')],
                'Cena zamknięcia': [p.get('close') for p in data.get('result')],
                'Giełda': ['FTX' for i in range(len(data.get('result')))]
            })
            return df
        return 'Brak danych dla tego okresu.'
    return data

@bp.route('/', methods=['GET', 'POST'])
def get_chart():
    """Return the price chart for a selected pair of cryptocurrencies from selected exchanges."""
    content = {'data': None}
    content['exchanges_list'] = get_exchanges_list(exchanges_urls)
    if request.method == 'POST':
        chart_data = pd.DataFrame(columns=['Czas', 'Cena zamknięcia', 'Giełda'])
        exchanges = request.form.getlist('ex')
        error = ''
        for ex in exchanges:
            params = {
                'symbol': get_symbol(request.form['coin1'], request.form['coin2'], request.form['ex']),
                'coin1': request.form['coin1'],
                'coin2': request.form['coin2'],
                'tf': ex_timeframes[ex]
            }
            data_url = get_data_url(**params, ex=ex)
            print(data_url)
            r = requests.get(data_url)
            data = r.json()
            ex_check = {
                'KuCoin': get_kucoin_data,
                'Binance': get_binance_data,
                'FTX': get_ftx_data
            }
            ret = ex_check.get(ex)(data)
            if isinstance(ret, pd.DataFrame):
                chart_data = pd.concat([chart_data, ret], ignore_index=True)
            else:
                error = ret
        if not chart_data.empty:
            fig = px.line(chart_data, x='Czas', y='Cena zamknięcia', color='Giełda', title=f'{params["symbol"]} chart')
            content['graph_json'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            content['data'] = {
                'symbol': params['symbol'],
                'ex': exchanges
            }
        flash(error)
    return render_template('index.html', **content)