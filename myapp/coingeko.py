import requests

def get_crypto_price(crypto_id, currency):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies={currency}"
    response = requests.get(url)
    data = response.json()
    return data[crypto_id][currency]

# Usage:
# price = get_crypto_price('bitcoin', 'usd')
# print(price)

def get_coin_data(search_query):
    api_url = f'https://api.coingecko.com/api/v3/search?query={search_query}'
    response = requests.get(api_url)
    search_results = response.json()
    try:
        data = search_results['coins'][0]
    except IndexError:
        return None
    coin_id = data['id']
    image = data['large']
    symbol = data['symbol']
    market_cap = data['market_cap_rank']
    return coin_id, image, symbol, market_cap,data


# def get_coin_data():
#     api_url = f'https://api.coingecko.com/api/v3/coins/markets?x_cg_demo_api_key=CG-KoDWqDuHCWkxgES3WWTuZtBT&vs_currency=usd&order=market_cap_desc'
#     response = requests.get(api_url)
#     search_results = response.json()
#     # print(search_results)
#     for index in search_results:
#         if index['symbol'] == 'btc':
#             print(index)
#
#
# get_coin_data()