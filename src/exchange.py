from datetime import datetime
from enum import Enum
from .webservice import YahooFinance, OpenExchangeRates

import json
import os


class UpdateFreq(Enum):
    NEVER = 'never'
    HOURLY = 'hourly'
    DAILY = 'daily'


class ExchangeRates():

    service = OpenExchangeRates()

    _file_path = None
    last_update = None
    update_freq = None
    _currencies = {}

    error = None

    def __init__(self, path, update_freq):
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
            self._currencies = self.service.load_from_url()
            self.last_update = datetime.now()
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

    def convert(self, amount, sources, destinations):
        results = []
        for source in sources:
            for destination in destinations:
                rate = self.rate(destination) / self.rate(source)
                convertedAmount = rate * amount
                formatted = '{0:.8f}'.format(convertedAmount).rstrip('0').rstrip('.')
                result = {
                    'amount': convertedAmount,
                    'source': source,
                    'destination': destination,
                    'title': formatted + ' ' + destination
                }
                results.append(result)
        return results
