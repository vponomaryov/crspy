import base64
import datetime
from http import server
import fnmatch
import json
import io
import os
import re
import sys
import time

import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot
import matplotlib.pyplot as plt

from crspy.collector import print_with_time

# TODO:
# - don't rebuild image if data are the same
# - save images to separate top dir?
# - include date of build to image?


def find_json_files(directory):
    for root, dirs, files in os.walk(directory):
        for basename in sorted(files):
            if fnmatch.fnmatch(basename, '*.json'):
                filename = os.path.join(root, basename)
                yield filename


def generate_images(path_to_month_dir):
    currecies = ('usd', 'euro')
    data = {
        currency: {
            'x_indexes': [],
            'x_sticks': [],
            'x': {'buy_max': [], 'sell_min': []},
            'y': {'buy': [], 'buy_max': [], 'sell': [], 'sell_min': []},
        } for currency in currecies
    }
    target_dir = os.path.join(
        os.path.abspath(path_to_month_dir), os.path.pardir)
    fileformat = 'png'

    for f in sorted(find_json_files(path_to_month_dir)):
        for currency in currecies:
            with open(f, 'r') as filedata:
                json_data = json.loads(filedata.read())
                ind_kurs = json_data['Индикативный курс']
                if currency == 'usd':
                    buy = int(ind_kurs['Доллар/Гривна']['they_buy'])
                    sell = int(ind_kurs['Доллар/Гривна']['they_sell'])
                else:
                    buy = int(ind_kurs['Евро/Гривна']['they_buy'])
                    sell = int(ind_kurs['Евро/Гривна']['they_sell'])

                date = datetime.datetime.strptime(
                    f.split('/')[-1].split('.')[0], '%Y_%m_%d__%H_%M_%S')
                date = date.strftime("%Y-%m-%d %H:%M")

                current_index = len(data[currency]['x_sticks'])
                if (len(data[currency]['y']['buy']) > 1 and
                        buy == data[currency]['y']['buy'][-1] and
                        buy == data[currency]['y']['buy'][-2] and
                        sell == data[currency]['y']['sell'][-1] and
                        sell == data[currency]['y']['sell'][-2]):
                    data[currency]['x_sticks'][-1] = date
                    data[currency]['y']['buy'][-1] = buy
                    data[currency]['y']['sell'][-1] = sell
                else:
                    current_index += 1
                    data[currency]['x_sticks'].append(date)
                    data[currency]['x_indexes'].append(current_index)
                    data[currency]['y']['buy'].append(buy)
                    data[currency]['y']['sell'].append(sell)

                for op, value in (('buy_max', buy), ('sell_min', sell)):
                    x = data[currency]['x'][op]
                    y = data[currency]['y'][op]
                    if y:
                        y0 = int(y[0])
                        func = y0.__gt__ if op == 'sell_min' else y0.__lt__
                        if func(value):
                            x.clear()
                            x.append(current_index)
                            y.clear()
                            y.append(value)
                        elif y0 == value:
                            x.append(current_index)
                            y.append(value)
                    else:
                        x.append(current_index)
                        y.append(value)

    for currency in currecies:
        CURRENCY = currency.upper()
        plt.figure(figsize=(18, 4.6))
        plt.title('%s rates' % CURRENCY)

        x = data[currency]['x_indexes']
        plt.xticks(x, data[currency]['x_sticks'], rotation=90, size='small')
        for op, color in (('sell', 'blue'), ('buy', 'red')):
            plt.plot(x, data[currency]['y'][op],
                     color=color, label='They %s' % op, linewidth=2)

        # Useful extremums (expensive buy, cheap selling)
        for op, color in (('sell_min', 'blue'), ('buy_max', 'red')):
            plt.plot(data[currency]['x'][op], data[currency]['y'][op],
                     color=color, marker='o', linestyle=' ')

        # Tweak spacing to prevent clipping of tick-labels
        plt.subplots_adjust(bottom=0.32)

        # Pad margins so that markers don't get clipped by the axes
        plt.margins(0.05)

        # Set grid
        plt.grid(
            b=True, which='both', color='grey', linestyle='-', linewidth=0.5)

        plt.xlabel('Date')
        plt.ylabel('Hryvnas / 100 %s' % CURRENCY)
        plt.legend()
        plt.tick_params(labeltop=False, labelright=True)

        filename = ''.join((
            '%s_' % currency, f.split("__")[0].split('/')[-1][:-3]))
        filepath = os.path.join(target_dir, filename)
        print_with_time('Creating image at %s.%s' % (filepath, fileformat))
        plt.savefig('%s.%s' % (filepath, fileformat), format=fileformat)
    plt.close('all')


def main():
    for ydirname in os.listdir('data'):
        if re.search('year_20[0-9]{2}$', ydirname):
            for mdirname in os.listdir('data/' + ydirname):
                if re.search('month_(0[1-9]{1}|1[0-2]{1})$', mdirname):
                    generate_images(
                        ''.join(['data', '/', ydirname, '/', mdirname]))


if __name__ == '__main__':
    main()
