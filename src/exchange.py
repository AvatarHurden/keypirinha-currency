from datetime import datetime
from enum import Enum
from .webservice import OpenExchangeRates, PrivateDomain

import json
import os


class UpdateFreq(Enum):
    NEVER = 'never'
    HOURLY = 'hourly'
    DAILY = 'daily'


class ExchangeRates():

    _file_path = None
    last_update = None
    update_freq = None
    _currencies = {}

    in_cur_fallback = 'USD'
    out_cur_fallback = 'EUR, GBP'

    default_curs_in = ['USD']
    default_curs_out = ['EUR', 'GBP']

    error = None

    def __init__(self, path, update_freq, plugin):
        self.plugin = plugin
        self.cheap_service = PrivateDomain(self.plugin)
        self.expensive_service = OpenExchangeRates(self.plugin)
        self.update_freq = update_freq
        self._file_path = os.path.join(path, 'rates.json')

        if os.path.exists(self._file_path):
            try:
                self.load_from_file()
            except Exception as e:
                self.update()
        else:
            self.update()

        self.tryUpdate()

    def shouldUpdate(self):
        time_diff = datetime.now() - self.last_update
        if self.update_freq.value == UpdateFreq.HOURLY.value:
            return time_diff.total_seconds() >= 3600
        elif self.update_freq.value == UpdateFreq.DAILY.value:
            return time_diff.days >= 1
        else:
            return False

    def tryUpdate(self):
        if not self.last_update:
            return True
        if self.shouldUpdate():
            return self.update()
        else:
            return False

    def update(self):
        try:
            try:
                self._currencies, update_time = self.cheap_service.load_from_url()
                self.last_update = datetime.now()
                time_diff = self.last_update - datetime.fromtimestamp(update_time)

                if (time_diff.total_seconds() > 3600 * 2):
                    self.plugin.info('cache server is more than 2 hours old. Requesting from main API')
                    self._currencies, update_time = self.expensive_service.load_from_url()
            except Exception as e:
                self.plugin.info('cache server has returned error. Requesting from main API')
                self._currencies, update_time = self.expensive_service.load_from_url()

            self.save_to_file()
            self.error = None
            return True
        except Exception as e:
            print(e)
            self.error = e
            return False

    def load_from_file(self):
        with open(self._file_path) as f:
            data = json.load(f)

        self.last_update = datetime.strptime(data['last_update'], '%Y-%m-%dT%H:%M:%S')
        self._currencies = data['rates']
        self._load_secondary_data()

    def _load_secondary_data(self):
        pass

    def save_to_file(self):
        data = {
            'rates': self._currencies,
            'last_update': self.last_update.strftime('%Y-%m-%dT%H:%M:%S')
        }

        with open(self._file_path, 'w') as f:
            json.dump(data, f)

    def rate(self, code):
        if code == 'USD':
            return 1
        else:
            return self._currencies[code]['price']

    def format_codes(self, codeString):
        lst = [x.strip() for x in codeString.split(',')]
        return lst

    def validate_codes(self, codeString):
        lst = self.format_codes(codeString)
        return [x.upper() for x in lst if x.upper() in self._currencies.keys()]

    def convert(self, query):
        results = []
        for destination in query['destinations']:
            total = query['extra'] if query['extra'] else 0
            for source in query['sources']:
                rate = self.rate(destination['currency']) / self.rate(source['currency'])
                convertedAmount = rate * source['amount']
                total += convertedAmount
                if source['amount'] == 1:
                    formatted = '{:,.8f}'.format(convertedAmount).rstrip('0').rstrip('.')
                else:
                    formatted = '{:,.2f}'.format(convertedAmount).rstrip('.')
            result = {
                'amount': total,
                'source': source['currency'],
                'destination': destination['currency'],
                'title': '{}'.format(total) + ' ' + destination['currency']
            }
            results.append(result)
        return results

    def _set_default_curs(self, string, isIn):
        lst = [x.strip() for x in string.split(',')]
        curs = [x.upper() for x in lst if x.upper() in self._currencies.keys()]
        if len(lst) != len(curs):
            return False
        if isIn:
            self.default_curs_in = curs
        else:
            self.default_curs_out = curs
        return True

    def set_default_curs_in(self, string):
        return self._set_default_curs(string, True)

    def set_default_curs_out(self, string):
        return self._set_default_curs(string, False)
