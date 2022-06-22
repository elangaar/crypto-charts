"""Script for comparing cryptocurrency charts from different sources."""

import json
import datetime
import pandas as pd
import plotly.express as px
import plotly.utils
import requests

from flask import (Blueprint, render_template, request, flash)

candles_data_params = {
    'KuCoin': {
        'separator': '-',
        'timeframes': ['1day'],
        'factor': 1
    },
    'Binance': {
        'separator': '',
        'timeframes': ['1d'],
        'factor': 1000
    },
    'FTX': {
        'separator': '/',
        'timeframes': [86400],
        'factor': 1
    }
}

candles_urls = {
    'KuCoin': 'https://api.kucoin.com/api/v1/market/candles?symbol={symbol}&type={timeframe}&startAt={start}&endAt={end}',
    'Binance': 'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeframe}&startTime={start}&endTime={end}',
    'FTX': 'https://ftx.com/api/markets/{symbol}/candles?resolution={timeframe}&start_time={start}&end_time={end}'
}

bp = Blueprint('coins', __name__)


def get_exchanges_list(ex):
    """Return a list of available exchanges"""
    return [ex for ex in ex.keys()]


def get_symbol(coin1, coin2, ex):
    """Return currency pair symbol."""
    return candles_data_params.get(ex)['separator'].join((coin1.upper(), coin2.upper()))


def get_data_url(ex, coin1, coin2, start_time=datetime.datetime.now() - datetime.timedelta(days=150),
                 end_time=datetime.datetime.now(), **kwargs):
    """Return the URL to an endpoint with historical price data from the exchange for specific pair of coins."""
    symbol = get_symbol(coin1, coin2, ex)
    timeframe = candles_data_params.get(ex)['timeframes'][0]
    start = str(int(float(datetime.datetime.timestamp(start_time)) * candles_data_params.get(ex)['factor']))
    end = str(int(float(datetime.datetime.timestamp(end_time)) * candles_data_params.get(ex)['factor']))
    url_string = candles_urls[ex].format(symbol=symbol, timeframe=timeframe, start=start, end=end)
    return url_string


def get_kucoin_data(data):
    """Return statistics and data chart from kucoin exchange."""
    if data.get('code') == '200000':
        if len(data.get('data')) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.fromtimestamp(int(t[0]) - 1) + datetime.timedelta(days=1) for t in
                         data.get('data')],
                'Cena zamknięcia': [float(p[2]) for p in data.get('data')],
                'Giełda': ['KuCoin' for i in range(len(data.get('data')))]
            })
            return df
        return 'Brak danych dla tego okresu.'
    return data


def get_binance_data(data):
    """Return statistics and data chart from binance exchange."""
    if type(data) == list:
        if len(data) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.fromtimestamp(float(t[6]) / 1000) for t in data],
                'Cena zamknięcia': [float(p[4]) for p in data],
                'Giełda': ['Binance' for i in range(len(data))]
            })
            return df
        return 'Brak danych dla tego okresu.'
    return data


def get_ftx_data(data):
    """Return statistics and data chart from FTX exchange."""
    if data.get('success') is True:
        if len(data.get('result')) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.strptime(t.get('startTime'), '%Y-%m-%dT%H:%M:%S%z') +
                         datetime.timedelta(hours=2, seconds=int(candles_data_params.get('FTX')['timeframes'][0])) for t
                         in data.get('result')],
                'Cena zamknięcia': [p.get('close') for p in data.get('result')],
                'Giełda': ['FTX' for i in range(len(data.get('result')))]
            })
            return df
        return 'Brak danych dla tego okresu.'
    return data


def get_chart(data, symbol):
    """Return a chart string to display on the page by plotly"""
    fig = px.line(data, x='Czas', y='Cena zamknięcia', color='Giełda', title=f'{symbol} chart')
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def get_api_data(url):
    """Return api data for chosen crypto pair and exchange."""
    r = requests.get(url)
    data = r.json()
    return data


def get_prepared_data(data, exchange):
    """Return prepared data for chosen crypto pair and exchange."""
    exchange_check = {
        'KuCoin': get_kucoin_data,
        'Binance': get_binance_data,
        'FTX': get_ftx_data
    }
    prepared_data = exchange_check.get(exchange)(data)
    return prepared_data


@bp.route('/', methods=['GET', 'POST'])
def main():
    """Return the price chart for a selected pair of cryptocurrencies from selected exchanges."""
    content = {
        'exchanges_list': get_exchanges_list(candles_data_params)
    }
    if request.method == 'POST':
        chart_data = pd.DataFrame(columns=['Czas', 'Cena zamknięcia', 'Giełda'])
        exchanges = request.form.getlist('exchanges')
        error = ''
        for exchange in exchanges:
            params = {
                'ex': exchange,
                'symbol': get_symbol(request.form['coin1'], request.form['coin2'], request.form['exchanges']),
                'coin1': request.form['coin1'],
                'coin2': request.form['coin2'],
                'tf': candles_data_params[exchange]['timeframes']
            }
            data_url = get_data_url(**params)
            api_data = get_api_data(data_url)
            prepared_data = get_prepared_data(api_data, exchange)
            if isinstance(prepared_data, pd.DataFrame):
                chart_data = pd.concat([chart_data, prepared_data], ignore_index=True)
            else:
                error = prepared_data
        if not chart_data.empty:
            content['graph_json'] = get_chart(chart_data, params['symbol'])
            content['symbol'] = params['symbol']
            content['exchanges'] = exchanges
        flash(error)
    return render_template('index.html', **content)
