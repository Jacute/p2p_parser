#!/usr/bin/python3.8
import json
from datetime import datetime

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import traceback
import requests
import time
import sys
# from random import random
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
# import re


software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)


def get_driver():
    try:
        options = webdriver.FirefoxOptions()
        options.set_preference("general.useragent.override",
                               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 OPR/73.0.3856.415 (Edition Yx GX)")

        options.set_preference("dom.webdriver.enabled", False)
        options.headless = True

        driver = webdriver.Firefox(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.implicitly_wait(5)
        return driver
    except Exception as e:
        print('Неудачная настройка браузера!')
        print(traceback.format_exc())
        print(input('Нажмите ENTER, чтобы закрыть эту программу'))
        sys.exit()


def parse_binance(url, headers, data):
    src = requests.post(url, headers=headers, json=data).text
    json_ = json.loads(src)
    price = json_['data'][0]['adv']['price']
    return price


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
    print(src)
    json_ = json.loads(src)
    price = json_['ads'][0]['price']
    return price


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


def parse_garantex(wallet):
    driver.get(f'https://garantex.io/trading/{wallet}')
    btn = driver.find_element(By.XPATH, f'//a[@id="{wallet}_tab"]')
    btn.click()
    tmp = driver.find_elements(By.XPATH, f'//tbody[@class="table table-hover {wallet}_ask asks"]/tr')[-1]
    sell_price = float(tmp.find_element(By.XPATH, './td').text.replace(' ', ''))
    tmp = driver.find_elements(By.XPATH, f'//tbody[@class="table table-hover {wallet}_bid bids"]/tr')[-1]
    buy_price = float(tmp.find_element(By.XPATH, './td').text.replace(' ', ''))
    return (buy_price, sell_price)


def main():
    dct = {'Binance': {'USDT': {}, 'BTC': {}, 'ETH': {}},
           'Kucoin': {'USDT': {}, 'BTC': {}, 'ETH': {}, 'USDC': {}},
           'Bybit': {'USDT': {}, 'BTC': {}, 'ETH': {}},
           'Huobi': {'USDT': {}, 'BTC': {}, 'ETH': {}},
           'Bitpapa': {'USDT': {}, 'BTC': {}, 'ETH': {}},
           'Garantex': {'USDT': {}, 'BTC': {}, 'ETH': {}, 'USDC': {}}}
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
                'payTypes': [],
                'proMerchantAds': False,
                'publisherType': None,
                'rows': 10,
                'tradeType': None
            }
            data['asset'] = i
            data['tradeType'] = j
            price = parse_binance('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers, data)
            dct['Binance'] = {**dct['Binance'], i: {**dct['Binance'][i], j: price}}

            price = parse_bybit(f'https://api2.bybit.com/spot/api/otc/item/list/?userId=&tokenId={i}&currencyId=RUB&payment=&side={0 if j == "SELL" else 1}&size=10&page=1&amount=', headers)
            dct['Bybit'] = {**dct['Bybit'], i: {**dct['Bybit'][i], j: price}}

            price = parse_huobi(f'https://otc-api.ri16.com/v1/data/trade-market?coinId={["BTC", "USDT", "ETH"].index(i) + 1}&currency=11&tradeType={"sell" if j == "BUY" else "buy"}&currPage=1&payMethod=0&acceptOrder=-1&country=&blockType=general&online=1&range=0&amount=&onlyTradable=false', headers)
            dct['Huobi'] = {**dct['Huobi'], i: {**dct['Huobi'][i], j: price}}

    for i in ['USDT', 'BTC', 'ETH', 'USDC']:
        for j in ['SELL', 'BUY']:
            headers = {
                'Accept': '*/*',
                'user_agent': user_agent,
            }
            price = parse_kucoin(f'https://www.kucoin.com/_api/otc/ad/list?currency={i}&side={j}&legal=RUB&page=1&pageSize=10&status=PUTUP&lang=ru_RU', headers)
            dct['Kucoin'] = {**dct['Kucoin'], i: {**dct['Kucoin'][i], 'SELL' if j == 'BUY' else 'BUY': price}}
    for i in ['USDT', 'BTC', 'ETH']:
        for j in ['sell', 'buy']:
            headers = {
                'Content-Type': 'application/json',
                'X-Access-Token': '5ZJffp7DTcFoFjknaVT-'
            }
            price = parse_bitpapa(
                f'https://bitpapa.com/api/v1/pro/search?crypto_amount=&type=sell&page=1&sort=price&currency_code=RUB&previous_currency_code=RUB&crypto_currency_code=ETH&with_correct_limits=false&limit=20',
                headers)
            dct['Bitpapa'] = {**dct['Bitpapa'], i: {**dct['Bitpapa'][i], 'SELL' if j == 'buy' else 'BUY': price}}
    btc_prices = parse_garantex('btcrub')
    if btc_prices == ('', ''):
        time.sleep(11111)
    eth_prices = parse_garantex('ethrub')
    usdt_prices = parse_garantex('usdtrub')
    usdc_prices = parse_garantex('usdcrub')
    dct['Garantex'] = {'BTC': {'BUY': btc_prices[0], 'SELL': btc_prices[1]},
                       'ETH': {'BUY': eth_prices[0], 'SELL': eth_prices[1]},
                       'USDT': {'BUY': usdt_prices[0], 'SELL': usdt_prices[1]},
                       'USDC': {'BUY': usdc_prices[0], 'SELL': usdc_prices[1]}}
    dct['time'] = str(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    with open('result.json', 'w') as f:
        json.dump(dct, f)
    print('Результаты успешно сохранены в result.json')


if __name__ == '__main__':
    driver = get_driver()
    while True:
        try:
            main()
        except Exception:
            print(traceback.format_exc())
            driver.close()
            driver.quit()
            driver = get_driver()
