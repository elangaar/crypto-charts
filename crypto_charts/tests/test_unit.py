from coins import get_exchanges_list


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
