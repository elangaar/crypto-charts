"""Script for comparing cryptocurrency charts from different sources."""

import json
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.utils
import requests

from flask import (Blueprint, render_template, request, flash)

COINS_LIST_URL = 'https://api.coingecko.com/api/v3/coins/list'
EXCHANGES_URLS = {
    'KuCoin': 'https://api.kucoin.com'
}
KUCOIN_URLS = {
    'stats_24': '/api/v1/market/stats?symbol=',
    'klines': '/api/v1/market/candles'
}
bp = Blueprint('coins', __name__)


def get_coins_list(url):
    """Return a list of available coins."""
    r = requests.get(url)
    return r.json()

def get_exchanges_list(ex):
    """Return a list of available exchanges"""
    return [ex for ex in ex.keys()]

@bp.route('/', methods=['GET', 'POST'])
def get_chart():
    """Return the price chart for a selected pair of cryptocurrencies from selected exchanges."""
    coins_list = get_coins_list(COINS_LIST_URL)
    exchanges_list = get_exchanges_list(EXCHANGES_URLS)
    params = None
    error = None
    if request.method == 'POST':
        params = {
            'start_time': datetime.now()-timedelta(days=1500),
            'end_time': datetime.now(),
            'coin1': request.form['coin1'],
            'coin2': request.form['coin2'],
            'exchange': request.form['exchange'],
            'curr_pair': '-'.join((request.form['coin1'].upper(), request.form['coin2'].upper())),
            'timeframe': ['1min', '3min', '5min', '15min', '30min', '1hour',
                          '2hour', '4hour', '6hour', '8hour', '12hour', '1day', '1week']
        }
        params['addr'] = EXCHANGES_URLS['KuCoin'] + \
            KUCOIN_URLS['klines'] + \
            '?symbol=' + params['curr_pair'] + \
            '&type=' + params['timeframe'][11] + \
            '&startAt=' + str(int(datetime.timestamp(params['start_time']))) + \
            '&endAt=' + str(int(datetime.timestamp(params['end_time'])))
        r = requests.get(params['addr'])
        data = r.json()
        params['data_code'] = data['code']
        if data['code'] == '400100':
            error = 'Błędny parametr'
        elif data['code'] == '200000':
            df = pd.DataFrame({
                'Czas': [datetime.fromtimestamp(float(t[0])) for t in data['data']],
                'Cena zamknięcia': [float(p[2]) for p in data['data']]
            })
            fig = px.line(df, x='Czas', y='Cena zamknięcia', title=f'{params["curr_pair"]} chart')
            graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            return render_template('index.html', params=params, graphJSON=graph_json, exchanges_list=exchanges_list)
        flash(error)
    return render_template('index.html', coins_list=coins_list, exchanges_list=exchanges_list, params=params)