import datetime
import fnmatch
import json
import os
import sys
import time

import pyvirtualdisplay
from selenium import webdriver
from selenium.webdriver.firefox import firefox_binary


URL = "http://kurs.kharkov.com"
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
COMMON_TABLE_XPATH = (
    "//div[contains(@class, 'left-table')]/div[@class='jsgrid']"
    "/div[@class='jsgrid-grid-body']/table[@class='jsgrid-table']")
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
    try:
        updated_at = browser.find_elements_by_xpath(
            "//div[@class='retail-exchange']/b")[0].text.split(': ')[-1]
    except IndexError as exc:
        print_with_time(
            "Failed to get 'updated_at' from the web page. "
            "Use current time for it.\n"
            "Error: %s" % str(exc))
        updated_at_dt = datetime.datetime.fromtimestamp(time.time())
    else:
        try:
            updated_at_dt = datetime.datetime.strptime(
                updated_at, '%d.%m.%Y - %H:%M')
        except ValueError:
            updated_at_dt = datetime.datetime.strptime(
                ' - '.join(updated_at.split(' ')[-2:]), '%d.%m.%Y - %H:%M')
    updated_at = updated_at_dt.strftime(TIME_FORMAT)
    print_with_time('Currency rates updated at ' + updated_at)

    collected_data = {}

    data = browser.find_elements_by_xpath(
        COMMON_TABLE_XPATH)[0].text.split('\n')
    # Old:
    # data = [
    #    'Индикативный курс', 'Покупка Продажа',
    #    'Доллар/Гривна 2635 2655', 'Евро/Гривна 3110 3150',
    #    'Рубль/Гривна 0.447 0.458', 'Евро/Доллар 1,182 1,19'
    # ]
    # New:
    # data = [
    #    'EUR/UAH 3050 3075', 'RUB/UAH 0.416 0.424',
    #    'EUR/USD 1,122 1,128', 'GBR/UAH', 'PLH/UAH', 'BYN/UAH'
    # ]
    parsed_data = {}
    for datum in data:
        datum = datum.lower()
        if not ('гривна' in datum or 'uah' in datum):
            continue
        if len(datum.split(' ')) != 3:
            continue
        currency_pair, they_buy, they_sell = datum.split(' ')
        parsed_data[currency_pair] = {
            'they_buy': they_buy,
            'they_sell': they_sell,
        }
    collected_data['Индикативный курс'] = parsed_data

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

    ############################ Processing data ##############################
    parsed_data_str = json.dumps(
        collected_data, indent=4, sort_keys=True, ensure_ascii=False)
    month = '%s' % updated_at_dt.month
    month = month if len(month) == 2 else '0' + month
    subdir = 'year_%s/month_%s/' % (updated_at_dt.year, month)
    dir_path = os.path.join(DATA_DIR, subdir)
    filename = updated_at.replace(
        ' ', '__').replace(':', '_').replace('-', '_') + '.json'
    file_path = os.path.join(dir_path, filename)

    # Read previous file and make sure that our new file is not duplicate
    if not os.path.exists(dir_path):
        print_with_time("Creating '%s' dir..." % dir_path)
        os.makedirs(dir_path)
    unique_data, sorted_files = True, sorted(os.listdir(dir_path))
    if (sorted_files and fnmatch.fnmatch(sorted_files[-1], '*.json')):
        with open(os.path.join(dir_path, sorted_files[-1]), 'r') as filedata:
            latest_json_data = json.loads(filedata.read())
        if latest_json_data == collected_data:
            unique_data = False

    # Write to file if not test mode
    if 'test' not in sys.argv[1:] and unique_data:
        print_with_time('Writing collected data to file %s' % file_path)
        with open(file_path, 'w') as datafile:
            datafile.write(parsed_data_str)
    else:
        print_with_time(
            "SKIP writing to file. "
            "Reason: 'test' arg is present and/or parsed data is "
            "the same as in the previous file.")

    print_with_time('Data: \n%s' % parsed_data_str)
    print_with_time('Successfully ended work, exiting.')


if __name__ == '__main__':
    main()
