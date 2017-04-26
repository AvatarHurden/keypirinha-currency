from datetime import datetime
import os

class ExchangeRates():

    url = "http://finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote?format=json"

    _file_path = None
    _rates = []
    _last_update = None

    def __init__(self, path):
        self._file_path = os.path.join(path, 'rates.json')

        if os.path.exists(self._file_path):
            self.load_from_file()
        else:
            self.load_from_url()
            self.save_to_file()

        if (datetime.now() - self._last_update).days >= 1:
            self.load_from_url()
            self.save_to_file()

    def load_from_file(self):
        with open(self._file_path) as f:
            data = json.load(f)

        self._last_update = datetime.strptime(data['last_update'], '%Y-%m-%dT%H:%M:%S')
        self._rates = data['rates']

    def save_to_file(self):
        data =  {
            'rates': self._rates,
            'last_update': self._last_update.strftime('%Y-%m-%dT%H:%M:%S')
        }

        with open(self._file_path, 'w') as f:
            json.dump(data, f)

    def load_from_url(self):
        opener = kpnet.build_urllib_opener()
        opener.addheaders = [("User-agent", "Mozilla/5.0")]
        with opener.open(self.url) as conn:
            response = conn.read()
        data = json.loads(response)
        rates = data['list']['resources']

        self._rates = []
        for rate in rates:
            fields = rate['resource']['fields']
            symbol = fields['symbol'][0:3]
            name = fields['name'].replace('USD/', '')
            price = float(fields['price'])

            private_rate = {
                'symbol': symbol,
                'name': name,
                'price': price
            }

            self._rates.append(private_rate)
        self._last_update = datetime.now()
