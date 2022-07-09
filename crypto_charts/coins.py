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

stats_urls = {
    'KuCoin': 'https://api.kucoin.com/api/v1/market/stats?symbol={symbol}',
    'Binance': 'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}',
    'FTX': 'https://ftx.com/api/markets/{symbol}?type=spot'
}

bp = Blueprint('coins', __name__)


def get_exchanges_list(ex):
    """Return a list of available exchanges"""
    return [ex for ex in ex.keys()]


def get_symbol(coin1, coin2, ex):
    """Return currency pair symbol."""
    return candles_data_params.get(ex)['separator'].join((coin1.upper(), coin2.upper()))


def get_data_urls(ex, coin1, coin2, start_time=datetime.datetime.now() - datetime.timedelta(days=10),
                 end_time=datetime.datetime.now(), **kwargs):
    """Return URLs to an endpoint with historical price data and current statistics from the exchange for specific pair of coins."""
    symbol = get_symbol(coin1, coin2, ex)
    timeframe = candles_data_params.get(ex)['timeframes'][0]
    start = str(int(float(datetime.datetime.timestamp(start_time)) * candles_data_params.get(ex)['factor']))
    end = str(int(float(datetime.datetime.timestamp(end_time)) * candles_data_params.get(ex)['factor']))
    url_candles = candles_urls[ex].format(symbol=symbol, timeframe=timeframe, start=start, end=end)
    url_stats = stats_urls[ex].format(symbol=symbol)
    return url_candles, url_stats


def get_kucoin_data(cand_vol_data, stats_data):
    """Return statistics and data for charts from kucoin exchange."""
    data = {}
    if stats_data.get('code') == '200000':
        data['stats_data'] = {
            'volume': stats_data['data']['vol'],
            'last_price': stats_data['data']['last'],
            'change_price_24': stats_data['data']['changePrice']
        }
    else:
        data['stats_data'] = stats_data
    if cand_vol_data.get('code') == '200000':
        if len(cand_vol_data.get('data')) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.fromtimestamp(int(t[0]) - 1) + datetime.timedelta(days=1) for t in
                         cand_vol_data.get('data')],
                'Cena zamknięcia': [float(p[2]) for p in cand_vol_data.get('data')],
                'Wolumen': [float(p[5]) for p in cand_vol_data.get('data')],
                'Giełda': ['KuCoin' for i in range(len(cand_vol_data.get('data')))]
            })
            data['charts_data'] = df
        else:
            data['charts_data'] = 'Brak danych dla tego okresu.'
    else:
        data['charts_data'] = cand_vol_data
    return data


def get_binance_data(cand_vol_data, stats_data):
    """Return statistics and data for charts from binance exchange."""
    data = {}
    if stats_data.get('code') is None:
        data['stats_data'] = {
            'volume': stats_data['volume'],
            'last_price': stats_data['lastPrice'],
            'change_price_24': stats_data['priceChange']
        }
    else:
        data['stats_data'] = stats_data
    if type(cand_vol_data) == list:
        if len(cand_vol_data) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.fromtimestamp(float(t[6]) / 1000) for t in cand_vol_data],
                'Cena zamknięcia': [float(p[4]) for p in cand_vol_data],
                'Wolumen': [float(p[5]) for p in cand_vol_data],
                'Giełda': ['Binance' for i in range(len(cand_vol_data))]
            })
            data['charts_data'] = df
        else:
            data['charts_data'] = 'Brak danych dla tego okresu.'
    else:
        data['charts_data'] = cand_vol_data
    return data


def get_ftx_data(cand_vol_data, stats_data):
    """Return statistics and data for charts from FTX exchange."""
    data = {}
    if stats_data.get('success') is True:
        data['stats_data'] = {
            'volume': stats_data['result']['quoteVolume24h']/stats_data['result']['price'],
            'last_price': stats_data['result']['last'],
            'change_price_24': stats_data['result']['change24h']*stats_data['result']['last']
        }
    else:
        data['stats_data'] = stats_data
    if cand_vol_data.get('success') is True:
        if len(cand_vol_data.get('result')) > 0:
            df = pd.DataFrame({
                'Czas': [datetime.datetime.strptime(t.get('startTime'), '%Y-%m-%dT%H:%M:%S%z') +
                         datetime.timedelta(hours=2, seconds=int(candles_data_params.get('FTX')['timeframes'][0])) for t
                         in cand_vol_data.get('result')],
                'Cena zamknięcia': [p.get('close') for p in cand_vol_data.get('result')],
                'Wolumen[USD]': [p.get('volume') for p in cand_vol_data.get('result')],
                'Giełda': ['FTX' for i in range(len(cand_vol_data.get('result')))]
            })
            df['Wolumen'] = df['Wolumen[USD]']/df['Cena zamknięcia']
            data['charts_data'] = df
        else:
            data['charts_data'] = 'Brak danych dla tego okresu.'
    else:
        data['charts_data'] = cand_vol_data
    return data

def get_price_chart(data, symbol):
    """Return a price chart string to display on the page by plotly"""
    fig = px.line(data, x='Czas', y='Cena zamknięcia', color='Giełda', title=f'Wykres ceny {symbol}')
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def get_vol_chart(data, symbol):
    """Return a volume chart string to display on the page by plotly"""
    fig = px.bar(data, x='Czas', y='Wolumen', color='Giełda', barmode='group', title=f'Wykres wolumenu {symbol}')
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def get_api_data(url):
    """Return data for chosen crypto pair and exchange."""
    r = requests.get(url)
    data = r.json()
    return data


def get_prepared_data(cand_vol_data, stats_data, exchange):
    """Return prepared data for chosen crypto pair and exchange."""
    exchange_check = {
        'KuCoin': get_kucoin_data,
        'Binance': get_binance_data,
        'FTX': get_ftx_data
    }
    prepared_data = exchange_check.get(exchange)(cand_vol_data, stats_data)
    return prepared_data


@bp.route('/', methods=['GET', 'POST'])
def main():
    """Return the price chart for a selected pair of cryptocurrencies from selected exchanges."""
    content = {
        'exchanges_list': get_exchanges_list(candles_data_params),
        'stats_data': {}
    }
    if request.method == 'POST':
        chart_data = pd.DataFrame(columns=['Czas', 'Cena zamknięcia', 'Wolumen', 'Giełda'])
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
            data_urls = get_data_urls(**params)
            cand_vol_api_data = get_api_data(data_urls[0])
            stats_api_data = get_api_data(data_urls[1])
            prepared_data = get_prepared_data(cand_vol_api_data, stats_api_data, exchange)

            if isinstance(prepared_data['stats_data'], dict):
                prepared_data['stats_data']['exchange'] = exchange
                content['stats_data'][exchange] = prepared_data['stats_data']
            else:
                error = prepared_data['stats_data']
            if isinstance(prepared_data['charts_data'], pd.DataFrame):
                chart_data = pd.concat([chart_data, prepared_data['charts_data']], ignore_index=True)
            else:
                error = prepared_data['charts_data']
        if not chart_data.empty:
            content['graph_price_json'] = get_price_chart(chart_data, params['symbol'])
            content['graph_vol_json'] = get_vol_chart(chart_data, params['symbol'])
            content['symbol'] = params['symbol']
            content['exchanges'] = exchanges
            content['quote_currency'] = request.form['coin2'].upper()
        flash(error)
    return render_template('index.html', **content)
