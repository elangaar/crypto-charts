from coins import get_exchanges_list, get_symbol, get_market


def test_get_exchanges_list():
    """
    GIVEN a dictionary with the names of exchanges as keys
    WHEN a list is created from dictionary keys
    THEN check type, length and 'KuCoin' value in return value
    """
    exchanges_urls = {
        'KuCoin': 'https://api.kucoin.com',
        'Binance': 'https://api.binance.com'
    }
    exchanges_list = get_exchanges_list(exchanges_urls)
    assert type(exchanges_list) == list
    assert len(exchanges_list) == 2
    assert 'KuCoin' in exchanges_list

def test_get_symbol():
    """
    GIVEN names of two coins and separator which depends on exchange
    WHEN url string and content data are created
    THEN check the correctness of the returned symbol
    """
    assert get_symbol('BTC', 'USDT', 'KuCoin') == 'BTC-USDT'
    assert get_symbol('BTC', 'USDT', 'Binance') == 'BTCUSDT'
    assert get_symbol('BTC', 'USDT', 'FTX') == 'BTC/USDT'
    assert get_symbol('btc', 'usdt', 'KuCoin') == 'BTC-USDT'
    assert get_symbol('btc', 'usdt', 'Binance') == 'BTCUSDT'
    assert get_symbol('btc', 'usdt', 'FTX') == 'BTC/USDT'

def test_get_market():
    """
    GIVEN symbol and market phrase pattern
    WHEN url string is created
    THEN get proper market part of the url string depending on exchange
    """
    klines_urls = {
        'KuCoin': '/api/v1/market/candles',
        'Binance': '/api/v3/klines',
        'FTX': '/markets/{market_name}/candles'
    }
    assert get_market(klines_urls['KuCoin'], 'BTC-USDT') == '/api/v1/market/candles?symbol=BTC-USDT&'
    assert get_market(klines_urls['Binance'], 'BTCUSDT') == '/api/v3/klines?symbol=BTCUSDT&'
    assert get_market(klines_urls['FTX'], 'BTC/USDT') == '/markets/BTC/USDT/candles?'
