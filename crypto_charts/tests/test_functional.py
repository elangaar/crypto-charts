from crypto_charts.coins import get_api_data, candles_urls


def test_main_get(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested by GET
    THEN check response
    """
    response = test_client.get('/')
    assert response.status_code == 200


def test_main_post(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page requested by POST
    THEN check response
    """
    form_data = {
        'pair': 'BTC-USDT',
    }
    response = test_client.post('/', data=form_data)
    assert response.status_code == 200


def test_get_api_data_success(sample_data):
    """
    GIVEN function and urls to exchanges APIs
    WHEN retrieve data from exchanges
    THEN check the correctness of the downloaded data
    """

    url_kucoin = candles_urls['KuCoin'].format(symbol='BTC-USDT', timeframe='1day', start='1642569817', end='1655526217')
    url_binance = candles_urls['Binance'].format(symbol='BTCUSDT', timeframe='1d', start='1642569817000', end='1655526217000')
    url_ftx = candles_urls['FTX'].format(symbol='BTC/USDT', timeframe='86400', start='1642569817', end='1655526217')

    data_kucoin = get_api_data(url_kucoin)
    data_binance = get_api_data(url_binance)
    data_ftx = get_api_data(url_ftx)

    assert sample_data['KuCoin']['code'] == data_kucoin['code']
    assert sample_data['KuCoin']['data'] == data_kucoin['data']

    assert sample_data['Binance'] == data_binance

    assert sample_data['FTX']['success'] == data_ftx['success']
    assert sample_data['FTX']['result'] == data_ftx['result']
