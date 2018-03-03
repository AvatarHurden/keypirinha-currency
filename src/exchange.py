from datetime import datetime
from enum import Enum

import keypirinha_net as kpnet
import json
import os

class UpdateFreq(Enum):
    NEVER = 'never'
    HOURLY = 'hourly'
    DAILY = 'daily'

class ExchangeRates():

    url = "http://finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote?format=json"

    _file_path = None
    last_update = None
    update_freq = None
    _currencies = {}

    def __init__(self, path, update_freq):
        self.update_freq = update_freq
        self._file_path = os.path.join(path, 'rates.json')

        if os.path.exists(self._file_path):
            try:
                self.load_from_file()
            except Exception as e:
                self.update()

        self.tryUpdate()

    def tryUpdate(self):
        time_diff = datetime.now() - self.last_update
        if (self.update_freq.value == UpdateFreq.HOURLY.value and time_diff.total_seconds() >= 3600) or (self.update_freq.value == UpdateFreq.DAILY.value and time_diff.days >= 1):
            self.update()
            return True
        else:
            return False

    def update(self):
        self.load_from_url()
        self.save_to_file()

    def load_from_file(self):
        with open(self._file_path) as f:
            data = json.load(f)

        self.last_update = datetime.strptime(data['last_update'], '%Y-%m-%dT%H:%M:%S')
        self._currencies = data['rates']
        self._load_secondary_data()

    def load_from_url(self):
        print("loading from url...")
        opener = kpnet.build_urllib_opener()
        opener.addheaders = [("User-agent", "Mozilla/5.0")]
        with opener.open(self.url) as conn:
            response = conn.read()
        data = json.loads(response)
        rates = data['list']['resources']

        self._currencies = {}
        for rate in rates:
            fields = rate['resource']['fields']
            symbol = fields['symbol'][0:3]
            name = fields['name'].replace('USD/', '')
            price = float(fields['price'])

            private_rate = {
                'name': name,
                'price': price
            }

            self._currencies[symbol] = private_rate
        self.last_update = datetime.now()
        self._load_secondary_data()

    def _load_secondary_data(self):
        pass

    def save_to_file(self):
        data =  {
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

    def validate_codes(self, codeString):
        lst = [x.strip() for x in codeString.split(',')]
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
