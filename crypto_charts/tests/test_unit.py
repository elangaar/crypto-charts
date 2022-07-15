from coins import get_list_from_dict, get_symbol


def test_get_exchanges_list():
    """
    GIVEN a dictionary with the names of exchanges as keys
    WHEN a list is created from dictionary keys
    THEN check type, length and 'KuCoin' and 'Binance' value in return value
    """
    exchanges_urls = {
        'KuCoin': 'https://api.kucoin.com',
        'Binance': 'https://api.binance.com'
    }
    exchanges_list = get_list_from_dict(exchanges_urls)
    assert type(exchanges_list) == list
    assert len(exchanges_list) == 2
    assert 'KuCoin' in exchanges_list
    assert 'Binance' in exchanges_list

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
