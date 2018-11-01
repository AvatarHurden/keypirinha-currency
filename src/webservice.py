import keypirinha_net as kpnet
import urllib
import json


class PrivateDomain():

    url = 'https://arthurvedana.com/currency/latest.json'

    def __init__(self, plugin):
        self.plugin = plugin

    def build_request(self):
        return self.url

    def load_from_url(self):
        self.plugin.info("loading from cache server...")
        opener = kpnet.build_urllib_opener()
        opener.addheaders = [("User-agent", "Mozilla/5.0")]

        requestURL = self.build_request()

        with opener.open(requestURL) as conn:
            response = conn.read()

        data = json.loads(response)
        rates = data['rates']

        currencies = {}
        for rate in rates:
            private_rate = {
                'name': rate,
                'price': rates[rate]
            }
            currencies[rate] = private_rate

        return currencies, data['timestamp']


class OpenExchangeRates():

    url = 'https://openexchangerates.org/api/latest.json'
    APPID = '462d6b7ade734ce1b59201196765d8d7'

    def __init__(self, plugin):
        self.plugin = plugin

    def build_request(self, parameters):
        return self.url + '?' + urllib.parse.urlencode(parameters)

    def load_from_url(self):
        self.plugin.info("loading from API...")
        opener = kpnet.build_urllib_opener()
        #opener.addheaders = [("User-agent", "Mozilla/5.0")]

        params = {'app_id': self.APPID,
                  'show_alternative': True}

        requestURL = self.build_request(params)

        with opener.open(requestURL) as conn:
            response = conn.read()

        data = json.loads(response)
        rates = data['rates']

        currencies = {}
        for rate in rates:
            private_rate = {
                'name': rate,
                'price': rates[rate]
            }
            currencies[rate] = private_rate

        return currencies, data['timestamp']
