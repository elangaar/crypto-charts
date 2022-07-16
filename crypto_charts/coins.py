"""Script for comparing cryptocurrency charts from different sources."""

import json
import datetime
import pandas as pd
import plotly.express as px
import plotly.utils
import re
import requests

from flask import (Blueprint, render_template, request, flash)

intervals_seconds = {
    '1 min': 60,
    '3 min': 180,
    '5 min': 300,
    '15 min': 900,
    '30 min': 1800,
    '1 hour': 3600,
    '2 hour': 7200,
    '4 hour': 14400,
    '6 hour': 21600,
    '8 hour': 28800,
    '12 hour': 43200,
    '1 day': 86400,
    '1 week': 7 * 86400,
    '1 month': 30 * 86400
}

candles_data_params = {
    'KuCoin': {
        'separator': '-',
        'timeframes': {'1 min': '1min',
                       '3 min': '3min',
                       '5 min': '5min',
                       '15 min': '15min',
                       '30 min': '30min',
                       '1 hour': '1hour',
                       '2 hour': '2hour',
                       '4 hour': '4hour',
                       '6 hour': '6hour',
                       '8 hour': '8hour',
                       '12 hour': '12hour',
                       '1 day': '1day',
                       '1 week': '1week',
                       },
        'factor': 1
    },
    'Binance': {
        'separator': '',
        'timeframes': {'1 min': '1m',
                       '3 min': '3m',
                       '5 min': '5m',
                       '15 min': '15m',
                       '30 min': '30m',
                       '1 hour': '1h',
                       '2 hour': '2h',
                       '4 hour': '4h',
                       '6 hour': '6h',
                       '8 hour': '8h',
                       '12 hour': '12h',
                       '1 day': '1d',
                       '1 week': '1w',
                       '1 month': '1M'
                       },
        'factor': 1000
    },
    'FTX': {
        'separator': '/',
        'timeframes': intervals_seconds,
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

exchanges_colors = {
    'KuCoin': 'darkblue',
    'Binance': 'darkorange',
    'FTX': 'green'
}

bp = Blueprint('coins', __name__)


def get_list_from_dict(d):
    """Return a list of keys from dict."""
    return [k for k in d.keys()]

def get_symbol(base_currency, quoote_currency, ex):
    """Return currency pair symbol."""
    return candles_data_params.get(ex)['separator'].join((base_currency.upper(), quoote_currency.upper()))


def get_data_urls(exchange, base_currency, quote_currency, begin_date, end_date, interval, **kwargs):
    """Return URLs to an endpoint with historical price data and current statistics from the exchange for specific pair of coins."""
    symbol = get_symbol(base_currency, quote_currency, exchange)
    start = str(int(float(datetime.datetime.timestamp(datetime.datetime.strptime(begin_date, '%Y-%m-%d'))) * candles_data_params.get(exchange)['factor']))
    end = str(int(float(datetime.datetime.timestamp(datetime.datetime.strptime(end_date, '%Y-%m-%d'))) * candles_data_params.get(exchange)['factor']))
    url_candles = candles_urls[exchange].format(symbol=symbol, timeframe=interval, start=start, end=end)
    url_stats = stats_urls[exchange].format(symbol=symbol)
    return url_candles, url_stats


def get_kucoin_data(cand_vol_data, stats_data, interval):
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
            time_stamp = pd.Series([datetime.datetime.fromtimestamp(int(t[0]) - 1 + intervals_seconds[interval]) for t in cand_vol_data.get('data')])
            df = pd.DataFrame({
                'Czas': pd.to_datetime(time_stamp),
                'Cena zamknięcia': [float(p[2]) for p in cand_vol_data.get('data')],
                'Wolumen': [float(p[5]) for p in cand_vol_data.get('data')],
                'Giełda': ['KuCoin' for i in range(len(cand_vol_data.get('data')))]
            })
            data['charts_data'] = df
        else:
            data['charts_data'] = 'KuCoin: brak danych dla tego okresu.'
    else:
        data['charts_data'] = f'KuCoin: {cand_vol_data.get("msg")}'
    return data


def get_binance_data(cand_vol_data, stats_data, interval=None):
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
            time_stamp = pd.Series([datetime.datetime.fromtimestamp(float(t[6]) / 1000) for t in cand_vol_data])
            df = pd.DataFrame({
                'Czas': pd.to_datetime(time_stamp).dt.floor('S'),
                'Cena zamknięcia': [float(p[4]) for p in cand_vol_data],
                'Wolumen': [float(p[5]) for p in cand_vol_data],
                'Giełda': ['Binance' for i in range(len(cand_vol_data))]
            })
            data['charts_data'] = df
        else:
            data['charts_data'] = 'Binance: brak danych dla tego okresu.'
    else:
        data['charts_data'] = f'Binance: {cand_vol_data.get("msg")}'
    return data


def get_ftx_data(cand_vol_data, stats_data, interval):
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
                'Czas': [datetime.datetime.fromtimestamp(datetime.datetime.timestamp(datetime.datetime.strptime(t.get('startTime'), '%Y-%m-%dT%H:%M:%S%z'))
                         + intervals_seconds[interval] - 1) for t in cand_vol_data.get('result')],
                'Cena zamknięcia': [p.get('close') for p in cand_vol_data.get('result')],
                'Wolumen[USD]': [p.get('volume') for p in cand_vol_data.get('result')],
                'Giełda': ['FTX' for i in range(len(cand_vol_data.get('result')))]
            })
            df['Wolumen'] = df['Wolumen[USD]']/df['Cena zamknięcia']
            data['charts_data'] = df
        else:
            data['charts_data'] = 'FTX: brak danych dla tego okresu.'
    else:
        data['charts_data'] = f'FTX: {cand_vol_data.get("error")}'
    return data


def get_price_chart(data, symbol):
    """Return a price chart string to display on the page by plotly"""
    fig = px.line(data, x='Czas', y='Cena zamknięcia', color='Giełda',
                  color_discrete_map=exchanges_colors,
                  title=f'Wykres ceny {symbol}')
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def get_vol_chart(data, symbol):
    """Return a volume chart string to display on the page by plotly"""
    fig = px.bar(data, x='Czas', y='Wolumen', color='Giełda', barmode='group',
                 color_discrete_map=exchanges_colors,
                 title=f'Wykres wolumenu {symbol}')
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def get_api_data(url):
    """Return data for chosen crypto pair and exchange."""
    r = requests.get(url)
    data = r.json()
    return data


def get_prepared_data(cand_vol_data, stats_data, exchange, interval):
    """Return prepared data for chosen crypto pair and exchange."""
    exchange_check = {
        'KuCoin': get_kucoin_data,
        'Binance': get_binance_data,
        'FTX': get_ftx_data
    }
    prepared_data = exchange_check.get(exchange)(cand_vol_data, stats_data, interval)
    return prepared_data


@bp.route('/', methods=['GET', 'POST'])
def main():
    """Return the price chart for a selected pair of cryptocurrencies from selected exchanges."""
    content = {
        'exchanges_list': get_list_from_dict(candles_data_params),
        'intervals_list': get_list_from_dict(intervals_seconds),
        'stats_data': {},
        'begin_date': datetime.date.today() - datetime.timedelta(days=10),
        'end_date': datetime.date.today()
    }
    if request.method == 'POST':
        chart_data = pd.DataFrame(columns=['Czas', 'Cena zamknięcia', 'Wolumen', 'Giełda'])
        exchanges = request.form.getlist('exchanges')
        pair = re.split("-", request.form['pair'])
        base_currency = pair[0]
        quote_currency = pair[1]
        error = ''
        for exchange in exchanges:
            try:
                interval = candles_data_params[exchange]['timeframes'][request.form.get('interval')]
            except KeyError:
                interval = None
            params = {
                'exchange': exchange,
                'symbol': get_symbol(base_currency, quote_currency, request.form['exchanges']),
                'base_currency': base_currency,
                'quote_currency': quote_currency,
                'interval': interval,
                'begin_date': request.form['begin-date'],
                'end_date': request.form['end-date']
            }
            data_urls = get_data_urls(**params)
            cand_vol_api_data = get_api_data(data_urls[0])
            stats_api_data = get_api_data(data_urls[1])
            prepared_data = get_prepared_data(cand_vol_api_data, stats_api_data, exchange, request.form['interval'])
            if isinstance(prepared_data['stats_data'], dict):
                prepared_data['stats_data']['exchange'] = exchange
                content['stats_data'][exchange] = prepared_data['stats_data']
            else:
                error = prepared_data['stats_data']
                flash(error)
            if isinstance(prepared_data['charts_data'], pd.DataFrame):
                chart_data = pd.concat([chart_data, prepared_data['charts_data']], ignore_index=True)
            else:
                error = prepared_data['charts_data']
                flash(error)
        if not chart_data.empty:
            content['graph_price_json'] = get_price_chart(chart_data, params['symbol'])
            content['graph_vol_json'] = get_vol_chart(chart_data, params['symbol'])
            content['symbol'] = params['symbol']
            content['exchanges'] = exchanges
            content['quote_currency'] = quote_currency.upper()
            content['exchanges_colors'] = exchanges_colors
    return render_template('index.html', **content)
