#!/usr/bin/python3.8
import json
from datetime import datetime

import traceback
import requests
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
import signal
from contextlib import contextmanager


class TimeoutException(Exception): pass


software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)


def parse_binance(url, headers, data):
    src = requests.post(url, headers=headers, json=data).text
    json_ = json.loads(src)
    price, url = '', ''
    for i in json_['data']:
        if i['adv']['tradeMethods']['tradeMethodName'] in binance_banks:
            price = i['adv']['price']
            url = f'https://p2p.binance.com/en/advertiserDetail?advertiserNo={i["advertiser"]["userNo"]}'
            break
    return price, url


def parse_kucoin(url, headers):
    src = requests.get(
        url,
        headers=headers).text
    json_ = json.loads(src)
    price = json_['items'][0]['floatPrice']
    return price


def parse_bitpapa(url, headers):
    src = requests.get(
        url,
        headers=headers).text
    json_ = json.loads(src)
    price = json_['ads'][0]['price']
    url = f'https://bitpapa.com/trade/new/{json_["ads"][0]["id"]}'
    return price, url


def parse_bybit(url, headers):
    src = requests.get(
        url,
        headers=headers).text
    json_ = json.loads(src)
    price = json_['result']['items'][0]['price']
    return price


def parse_huobi(url, headers):
    src = requests.get(
        url,
        headers=headers).text
    json_ = json.loads(src)
    price = json_['data'][0]['price']
    return price


def main():
    dct = {'Binance': {'USDT': {}, 'BTC': {}, 'ETH': {}},
           'Kucoin': {'USDT': {}, 'BTC': {}, 'ETH': {}, 'USDC': {}},
           'Bybit': {'USDT': {}, 'BTC': {}, 'ETH': {}},
           'Huobi': {'USDT': {}, 'BTC': {}, 'ETH': {}},
           'Bitpapa': {'USDT': {}, 'BTC': {}, 'ETH': {}}}
    for i in ['BTC', 'USDT', 'ETH']:
        for j in ['BUY', 'SELL']:
            user_agent = user_agent_rotator.get_random_user_agent()
            headers = {
                'Accept': '*/*',
                "Content-type": 'application/json',
                'user_agent': user_agent,
            }
            data = {
                'asset': None,
                'countries': [],
                'fiat': "RUB",
                'page': 1,
                'payTypes': binance_banks,
                'proMerchantAds': False,
                'publisherType': None,
                'rows': 10,
                'tradeType': None
            }
            data['asset'] = i
            data['tradeType'] = j
            price, url = parse_binance('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers, data)
            dct['Binance'] = {**dct['Binance'], i: {**dct['Binance'][i], j: {'price': float(price), 'url': url}}}

            price = parse_bybit(f'https://api2.bybit.com/spot/api/otc/item/list/?userId=&tokenId={i}&currencyId=RUB&payment=&side={0 if j == "SELL" else 1}&size=10&page=1&amount=', headers)
            dct['Bybit'] = {**dct['Bybit'], i: {**dct['Bybit'][i], j: float(price)}}

            price = parse_huobi(f'https://otc-api.ri16.com/v1/data/trade-market?coinId={["BTC", "USDT", "ETH"].index(i) + 1}&currency=11&tradeType={"sell" if j == "BUY" else "buy"}&currPage=1&payMethod=0&acceptOrder=-1&country=&blockType=general&online=1&range=0&amount=&onlyTradable=false', headers)
            dct['Huobi'] = {**dct['Huobi'], i: {**dct['Huobi'][i], j: float(price)}}

    for i in ['USDT', 'BTC', 'ETH', 'USDC']:
        for j in ['SELL', 'BUY']:
            headers = {
                'Accept': '*/*',
                'user_agent': user_agent,
            }
            price = parse_kucoin(f'https://www.kucoin.com/_api/otc/ad/list?currency={i}&side={j}&legal=RUB&page=1&pageSize=10&status=PUTUP&lang=ru_RU', headers)
            dct['Kucoin'] = {**dct['Kucoin'], i: {**dct['Kucoin'][i], 'SELL' if j == 'BUY' else 'BUY': float(price)}}
    for i in ['USDT', 'BTC', 'ETH']:
        for j in ['sell', 'buy']:
            headers = {
                'Content-Type': 'application/json',
                'X-Access-Token': '5ZJffp7DTcFoFjknaVT-'
            }
            price, url = parse_bitpapa(
                f'https://bitpapa.com/api/v1/pro/search?crypto_amount=&currency_code=RUB&crypto_currency_code={i}&with_correct_limits=false&sort={"" if j == "sell" else "-"}price&type={j}&page=1&limit=20&previous_currency_code=RUB&pages=23&total=20',
                headers)
            dct['Bitpapa'] = {**dct['Bitpapa'], i: {**dct['Bitpapa'][i], 'SELL' if j == 'buy' else 'BUY': {'price': float(price), 'url': url}}}

    dct['time'] = str(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    with open('result.json', 'w') as f:
        json.dump(dct, f)
    print('Результаты успешно сохранены в result.json', dct['time'])


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    binance_banks = ['RosBankNew', 'RaiffeisenBank', 'PostBankNew', 'BCSBank', 'QIWI', 'TinkoffNew', 'UralsibBank', 'MTSBank']
    while True:
        try:
            with time_limit(120):
                main()
        except TimeoutException as e:
            print("Timed out!")
        except Exception:
            print(traceback.format_exc())
