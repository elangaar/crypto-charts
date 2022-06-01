"""Script for comparing cryptocurrency charts from different sources."""

import json
import datetime

import pandas as pd
import plotly.express as px
import plotly.utils
import requests

from flask import (Blueprint, render_template, request, flash)

COINS_LIST_URL = 'https://api.coingecko.com/api/v3/coins/list'
exchanges_urls = {
    'KuCoin': 'https://api.kucoin.com',
    'Binance': 'https://api.binance.com'
}
klines_urls = {
    'KuCoin': '/api/v1/market/candles',
    'Binance': '/api/v3/klines'
}
ex_pair_separator = {
    'KuCoin': '-',
    'Binance': ''
}
ex_interval_phrase = {
    'KuCoin': 'type',
    'Binance': 'interval'
}
ex_time_phrase = {
    'start': {
        'KuCoin': 'startAt',
        'Binance': 'startTime'
    },
    'end': {
        'KuCoin': 'endAt',
        'Binance': 'endTime'
    }
}
ex_timeframes = {
    'KuCoin': '1day',
    'Binance': '1d'
}
ex_factor = {
    'KuCoin': 1,
    'Binance': 1000
}

bp = Blueprint('coins', __name__)


def get_coins_list(url):
    """Return a list of available coins."""
    r = requests.get(url)
    return r.json()

def get_exchanges_list(ex):
    """Return a list of available exchanges"""
    return [ex for ex in ex.keys()]

def get_symbol(coin1, coin2, ex):
    """Return currency pair symbol."""
    return ex_pair_separator[ex].join((coin1.upper(), coin2.upper()))

def get_data_url(coin1, coin2, ex, tf, start_time=datetime.datetime.now()-datetime.timedelta(days=30), end_time=datetime.datetime.now(), symbol=None) :
    """"Return the URL to an endpoint with data from the exchange."""
    symbol = get_symbol(coin1, coin2, ex)
    start_time = str(int(float(datetime.datetime.timestamp(start_time)) * ex_factor[ex]))
    end_time = str(int(float(datetime.datetime.timestamp(end_time)) * ex_factor[ex]))
    url_string = exchanges_urls[ex] + klines_urls[ex] + '?symbol=' + symbol + '&' + ex_interval_phrase[ex] + '=' + tf + \
        '&' + ex_time_phrase['start'][ex] + '=' + start_time + '&' + ex_time_phrase['end'][ex] + '=' + end_time
    return url_string

def get_kucoin_data(data):
    """Return statistics data and data chart from kucoin exchange."""
    if data['code'] == '200000':
        df = pd.DataFrame({
            'Czas': [datetime.datetime.fromtimestamp(int(t[0])-1)+datetime.timedelta(days=1) for t in data['data']],
            'Cena zamknięcia': [float(p[2]) for p in data['data']]
        })
        return df
    return data

def get_binance_data(data):
    """Return statistics data and data chart from binance exchange."""
    df = pd.DataFrame({
        'Czas': [datetime.datetime.fromtimestamp(float(t[6])/1000) for t in data],
        'Cena zamknięcia': [float(p[4]) for p in data]
    })
    return df

@bp.route('/', methods=['GET', 'POST'])
def get_chart():
    """Return the price chart for a selected pair of cryptocurrencies from selected exchanges."""
    coins_list = get_coins_list(COINS_LIST_URL)
    exchanges_list = get_exchanges_list(exchanges_urls)
    if request.method == 'POST':
        params = {
            'symbol': get_symbol(request.form['coin1'], request.form['coin2'], request.form['ex']),
            'coin1': request.form['coin1'],
            'coin2': request.form['coin2'],
            'ex': request.form['ex'],
            'tf': ex_timeframes[request.form['ex']]
        }
        data_url = get_data_url(**params)
        print(data_url)
        r = requests.get(data_url)
        data = r.json()
        ex_check = {
            'KuCoin': get_kucoin_data,
            'Binance': get_binance_data
        }
        ret = ex_check[params['ex']](data)
        if isinstance(ret, pd.DataFrame):
            fig = px.line(ret, x='Czas', y='Cena zamknięcia', title=f'{params["symbol"]} chart')
            graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            content_data = {
                'symbol': params['symbol'],
                'ex': params['ex']
            }
            return render_template('index.html', data=content_data, graphJSON=graph_json, exchanges_list=exchanges_list)
        else:
            error = ret
        flash(error)
    return render_template('index.html', coins_list=coins_list, exchanges_list=exchanges_list, data=None)