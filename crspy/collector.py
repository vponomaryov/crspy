import datetime
import json
import os
import sys
import time

import pyvirtualdisplay
from selenium import webdriver
from selenium.webdriver.firefox import firefox_binary


URL = "http://kurs.kharkov.com"
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
RETAIL_TABLE_XPATH = (
    "//div[@class='retail-exchange']/table[@class='features-table']")
COMMON_TABLE_XPATH = (
    "//div[@class='wholesale-exchange']/table[@class='features-table']")
DATA_DIR = os.path.abspath(__file__ + "/../../data")
FF_BIN_DEFAULT_PATH = '~/Documents/32bit/firefox/firefox'


def get_current_time():
    return datetime.datetime.fromtimestamp(time.time()).strftime(TIME_FORMAT)


def print_with_time(text):
    current_time = get_current_time()
    print(current_time + ' - ' + text)


def main():
    ############################# Loading data ################################
    print_with_time('Configuring display...')
    display = pyvirtualdisplay.Display(visible=0, size=(800, 600))
    display.start()

    FF_BIN_PATH = FF_BIN_DEFAULT_PATH
    for arg in sys.argv[1:]:
        if arg.startswith('bin='):
            FF_BIN_PATH = arg.split('=')[-1]
            break

    print_with_time("Starting FireFox from '%s' binary..." % FF_BIN_PATH)
    if FF_BIN_PATH.startswith('~'):
        FF_BIN_PATH = os.path.expanduser('~') + FF_BIN_PATH[1:]
    ff_bin = firefox_binary.FirefoxBinary(FF_BIN_PATH)
    browser = webdriver.Firefox(firefox_binary=ff_bin)

    print_with_time('Downloading web page...')
    browser.get(URL)

    print_with_time('Downloaded web page at ' + get_current_time())

    ############################# Parsing data ################################
    updated_at = browser.find_elements_by_xpath(
        "//div[@class='retail-exchange']/b")[0].text.split(': ')[-1]

    updated_at_dt = datetime.datetime.strptime(updated_at, '%d.%m.%Y - %H:%M')
    updated_at = updated_at_dt.strftime(TIME_FORMAT)
    print_with_time('Currency rates updated at ' + updated_at)

    collected_data = {}

    for xpath in (RETAIL_TABLE_XPATH, COMMON_TABLE_XPATH):
        data = browser.find_elements_by_xpath(xpath)[0].text.split('\n')
        # data = [
        #    'Индикативный курс', 'Покупка Продажа',
        #    'Доллар/Гривна 2635 2655', 'Евро/Гривна 3110 3150',
        #    'Рубль/Гривна 0.447 0.458', 'Евро/Доллар 1,182 1,19'
        # ]
        parsed_data = {}
        for datum in data[1:]:
            if 'Гривна' in datum:
                currency_pair, they_buy, they_sell = datum.split(' ')
                parsed_data[currency_pair] = {
                    'they_buy': they_buy,
                    'they_sell': they_sell,
                }
        collected_data[data[0]] = parsed_data

    ############################ Terminate webdriver ##########################
    try:
        browser.quit()
    except Exception as e:
        print_with_time(
            'Caught following exception trying QUIT browser: %s' % e)
        try:
            browser.close()
        except Exception as e:
            print_with_time(
                'Caught following exception trying CLOSE browser: %s' % e)

    ############################# Handling data ###############################
    parsed_data_str = json.dumps(
        collected_data, indent=4, sort_keys=True, ensure_ascii=False)

    # Write to file if not test mode
    if 'test' not in sys.argv[1:]:
        month = '%s' % updated_at_dt.month
        month = month if len(month) == 2 else '0' + month
        subdir = 'year_%s/month_%s/' % (updated_at_dt.year, month)
        filename = updated_at.replace(
            ' ', '__').replace(':', '_').replace('-', '_') + '.json'
        dir_path = os.path.join(DATA_DIR, subdir)
        file_path = os.path.join(dir_path, filename)
        print_with_time('Writing collected data to file %s' % file_path)
        if not os.path.exists(dir_path):
            print_with_time("Creating '%s' dir..." % dir_path)
            os.makedirs(dir_path)
        with open(file_path, 'w') as datafile:
            datafile.write(parsed_data_str)
    else:
        print_with_time("Found 'test' arg, skipping writing to file.")

    print_with_time('Data: \n%s' % parsed_data_str)
    print_with_time('Successfully ended work, exiting.')


if __name__ == '__main__':
    main()
