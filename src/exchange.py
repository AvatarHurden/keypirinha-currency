from datetime import datetime

class ExchangeRates():

    url = "http://finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote?format=json"

    cache_path = ""
    _rates = []
    _last_update = datetime.now()

    def __init__(self, path):
        self.cache_path = path

        self.load_from_url()

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
