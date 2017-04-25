# Keypirinha launcher (keypirinha.com)

import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet

from . import exchange

import re
import json
import traceback
import urllib.error
import urllib.parse
from html.parser import HTMLParser

class Currency(kp.Plugin):
    """
    One-line description of your plugin.

    This block is a longer and more detailed description of your plugin that may
    span on several lines, albeit not being required by the application.

    You may have several plugins defined in this module. It can be useful to
    logically separate the features of your package. All your plugin classes
    will be instantiated by Keypirinha as long as they are derived directly or
    indirectly from :py:class:`keypirinha.Plugin` (aliased ``kp.Plugin`` here).

    In case you want to have a base class for your plugins, you must prefix its
    name with an underscore (``_``) to indicate Keypirinha it is not meant to be
    instantiated directly.

    In rare cases, you may need an even more powerful way of telling Keypirinha
    what classes to instantiate: the ``__keypirinha_plugins__`` global variable
    may be declared in this module. It can be either an iterable of class
    objects derived from :py:class:`keypirinha.Plugin`; or, even more dynamic,
    it can be a callable that returns an iterable of class objects. Check out
    the ``StressTest`` example from the SDK for an example.

    Up to 100 plugins are supported per module.

    More detailed documentation at: http://keypirinha.com/api/plugin.html
    """

    currencies = {
        'AED': 'United Arab Emirates Dirham',
        'AFN': 'Afghanistan Afghani',
        'ALL': 'Albania Lek',
        'AMD': 'Armenia Dram',
        'ANG': 'Netherlands Antilles Guilder',
        'AOA': 'Angola Kwanza',
        'ARS': 'Argentina Peso',
        'AUD': 'Australia Dollar',
        'AWG': 'Aruba Guilder',
        'AZN': 'Azerbaijan New Manat',
        'BAM': 'Bosnia and Herzegovina Convertible Marka',
        'BBD': 'Barbados Dollar',
        'BDT': 'Bangladesh Taka',
        'BGN': 'Bulgaria Lev',
        'BHD': 'Bahrain Dinar',
        'BIF': 'Burundi Franc',
        'BMD': 'Bermuda Dollar',
        'BND': 'Brunei Darussalam Dollar',
        'BOB': 'Bolivia Bolíviano',
        'BRL': 'Brazil Real',
        'BSD': 'Bahamas Dollar',
        'BTN': 'Bhutan Ngultrum',
        'BWP': 'Botswana Pula',
        'BYN': 'Belarus Ruble',
        'BZD': 'Belize Dollar',
        'CAD': 'Canada Dollar',
        'CDF': 'Congo/Kinshasa Franc',
        'CHF': 'Switzerland Franc',
        'CLP': 'Chile Peso',
        'CNY': 'China Yuan Renminbi',
        'COP': 'Colombia Peso',
        'CRC': 'Costa Rica Colon',
        'CUC': 'Cuba Convertible Peso',
        'CUP': 'Cuba Peso',
        'CVE': 'Cape Verde Escudo',
        'CZK': 'Czech Republic Koruna',
        'DJF': 'Djibouti Franc',
        'DKK': 'Denmark Krone',
        'DOP': 'Dominican Republic Peso',
        'DZD': 'Algeria Dinar',
        'EGP': 'Egypt Pound',
        'ERN': 'Eritrea Nakfa',
        'ETB': 'Ethiopia Birr',
        'EUR': 'Euro Member Countries',
        'FJD': 'Fiji Dollar',
        'FKP': 'Falkland Islands (Malvinas) Pound',
        'GBP': 'United Kingdom Pound',
        'GEL': 'Georgia Lari',
        'GGP': 'Guernsey Pound',
        'GHS': 'Ghana Cedi',
        'GIP': 'Gibraltar Pound',
        'GMD': 'Gambia Dalasi',
        'GNF': 'Guinea Franc',
        'GTQ': 'Guatemala Quetzal',
        'GYD': 'Guyana Dollar',
        'HKD': 'Hong Kong Dollar',
        'HNL': 'Honduras Lempira',
        'HRK': 'Croatia Kuna',
        'HTG': 'Haiti Gourde',
        'HUF': 'Hungary Forint',
        'IDR': 'Indonesia Rupiah',
        'ILS': 'Israel Shekel',
        'IMP': 'Isle of Man Pound',
        'INR': 'India Rupee',
        'IQD': 'Iraq Dinar',
        'IRR': 'Iran Rial',
        'ISK': 'Iceland Krona',
        'JEP': 'Jersey Pound',
        'JMD': 'Jamaica Dollar',
        'JOD': 'Jordan Dinar',
        'JPY': 'Japan Yen',
        'KES': 'Kenya Shilling',
        'KGS': 'Kyrgyzstan Som',
        'KHR': 'Cambodia Riel',
        'KMF': 'Comoros Franc',
        'KPW': 'Korea (North) Won',
        'KRW': 'Korea (South) Won',
        'KWD': 'Kuwait Dinar',
        'KYD': 'Cayman Islands Dollar',
        'KZT': 'Kazakhstan Tenge',
        'LAK': 'Laos Kip',
        'LBP': 'Lebanon Pound',
        'LKR': 'Sri Lanka Rupee',
        'LRD': 'Liberia Dollar',
        'LSL': 'Lesotho Loti',
        'LYD': 'Libya Dinar',
        'MAD': 'Morocco Dirham',
        'MDL': 'Moldova Leu',
        'MGA': 'Madagascar Ariary',
        'MKD': 'Macedonia Denar',
        'MMK': 'Myanmar (Burma) Kyat',
        'MNT': 'Mongolia Tughrik',
        'MOP': 'Macau Pataca',
        'MRO': 'Mauritania Ouguiya',
        'MUR': 'Mauritius Rupee',
        'MVR': 'Maldives (Maldive Islands) Rufiyaa',
        'MWK': 'Malawi Kwacha',
        'MXN': 'Mexico Peso',
        'MYR': 'Malaysia Ringgit',
        'MZN': 'Mozambique Metical',
        'NAD': 'Namibia Dollar',
        'NGN': 'Nigeria Naira',
        'NIO': 'Nicaragua Cordoba',
        'NOK': 'Norway Krone',
        'NPR': 'Nepal Rupee',
        'NZD': 'New Zealand Dollar',
        'OMR': 'Oman Rial',
        'PAB': 'Panama Balboa',
        'PEN': 'Peru Sol',
        'PGK': 'Papua New Guinea Kina',
        'PHP': 'Philippines Peso',
        'PKR': 'Pakistan Rupee',
        'PLN': 'Poland Zloty',
        'PYG': 'Paraguay Guarani',
        'QAR': 'Qatar Riyal',
        'RON': 'Romania New Leu',
        'RSD': 'Serbia Dinar',
        'RUB': 'Russia Ruble',
        'RWF': 'Rwanda Franc',
        'SAR': 'Saudi Arabia Riyal',
        'SBD': 'Solomon Islands Dollar',
        'SCR': 'Seychelles Rupee',
        'SDG': 'Sudan Pound',
        'SEK': 'Sweden Krona',
        'SGD': 'Singapore Dollar',
        'SHP': 'Saint Helena Pound',
        'SLL': 'Sierra Leone Leone',
        'SOS': 'Somalia Shilling',
        'SPL*': 'Seborga Luigino',
        'SRD': 'Suriname Dollar',
        'STD': 'São Tomé and Príncipe Dobra',
        'SVC': 'El Salvador Colon',
        'SYP': 'Syria Pound',
        'SZL': 'Swaziland Lilangeni',
        'THB': 'Thailand Baht',
        'TJS': 'Tajikistan Somoni',
        'TMT': 'Turkmenistan Manat',
        'TND': 'Tunisia Dinar',
        'TOP': "Tonga Pa'anga",
        'TRY': 'Turkey Lira',
        'TTD': 'Trinidad and Tobago Dollar',
        'TVD': 'Tuvalu Dollar',
        'TWD': 'Taiwan New Dollar',
        'TZS': 'Tanzania Shilling',
        'UAH': 'Ukraine Hryvnia',
        'UGX': 'Uganda Shilling',
        'USD': 'United States Dollar',
        'UYU': 'Uruguay Peso',
        'UZS': 'Uzbekistan Som',
        'VEF': 'Venezuela Bolivar',
        'VND': 'Viet Nam Dong',
        'VUV': 'Vanuatu Vatu',
        'WST': 'Samoa Tala',
        'XAF': 'Communauté Financière Africaine (BEAC) CFA Franc BEAC',
        'XCD': 'East Caribbean Dollar',
        'XDR': 'International Monetary Fund (IMF) Special Drawing Rights',
        'XOF': 'Communauté Financière Africaine (BCEAO) Franc',
        'XPF': 'Comptoirs Français du Pacifique (CFP) Franc',
        'YER': 'Yemen Rial',
        'ZAR': 'South Africa Rand',
        'ZMW': 'Zambia Kwacha',
        'ZWD': 'Zimbabwe Dollar'
    }

    API_URL = "http://query.yahooapis.com/v1/public/yql"
    API_USER_AGENT = "Mozilla/5.0"

    ITEMCAT_CONVERT = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 2

    DEFAULT_SECTION = 'defaults'

    DEFAULT_ITEM_ENABLED = True
    DEFAULT_ITEM_LABEL = 'Convert Currency'
    DEFAULT_CUR_IN = 'USD'
    DEFAULT_CUR_OUT = 'EUR, GBP'

    default_item_enabled = DEFAULT_ITEM_ENABLED
    default_item_label = DEFAULT_ITEM_LABEL
    default_cur_in = DEFAULT_CUR_IN
    default_cur_out = DEFAULT_CUR_OUT

    ACTION_COPY_RESULT = 'copy_result'
    ACTION_COPY_AMOUNT = 'copy_amount'

    def __init__(self):
        super().__init__()

    def on_start(self):
        self._read_config()

        rates = ExchangeRates(self.get_package_cache_path())
        
        actions = [
            self.create_action(
                name=self.ACTION_COPY_AMOUNT,
                label="Copy result",
                short_desc="Copy the result to clipboard"),
            self.create_action(
                name=self.ACTION_COPY_RESULT,
                label="Copy result with code",
                short_desc="Copy result (with code) to clipboard")]

        self.set_actions(self.ITEMCAT_RESULT, actions)

    def on_catalog(self):
        catalog = []
        if self.default_item_enabled:
            catalog.append(self._create_translate_item(
                label=self.default_item_label))
        self.set_catalog(catalog)

    def on_suggest(self, user_input, items_chain):
        if not items_chain or items_chain[-1].category() != self.ITEMCAT_CONVERT:
            return
        suggestions = []

        if self.should_terminate(0.25):
            return
        try:
            query = self._parse_and_merge_input(user_input)
            if not query['from_cur'] or not query['to_cur'] or not user_input:
                return

            # get translated version of terms
            opener = kpnet.build_urllib_opener()
            opener.addheaders = [("User-agent", self.API_USER_AGENT)]
            url = self._build_api_url(query['from_cur'], query['to_cur'], query['amount'])
            with opener.open(url) as conn:
                response = conn.read()
            if self.should_terminate():
                return

            # parse response from the api
            results = self._parse_api_response(response, query)

            for (label, source, dest) in results:
                suggestions.append(self._create_result_item(
                    label=label,
                    short_desc= source + ' to ' + dest,
                    target=label
                ))
        except Exception as exc:
            suggestions.append(self.create_error_item(
            label=user_input,
            short_desc="Error: " + str(exc)))

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
        # else
        #     suggestions = [self._create_keyword_item(
        #         label=user_input,
        #         short_desc="Convert values between currencies")]
        #     self.set_suggestions(suggestions)

    def on_execute(self, item, action):
        if item.category() != self.ITEMCAT_RESULT:
            return

        # browse or copy url
        if action and action.name() == self.ACTION_COPY_AMOUNT:
            amount = item.data_bag()[:-4]

            kpu.set_clipboard(amount)
        # default action: copy result (ACTION_COPY_RESULT)
        else:
            kpu.set_clipboard(item.data_bag())

    def on_activated(self):
        pass

    def on_deactivated(self):
        pass

    def on_events(self, flags):
        if flags & (kp.Events.APPCONFIG | kp.Events.PACKCONFIG |
                    kp.Events.NETOPTIONS):
            self._read_config()
            self.on_catalog()

    def _parse_and_merge_input(self, user_input=None):
        query = {
            'from_cur': self.default_cur_in,
            'to_cur': self.default_cur_out,
            'amount': 1}

        # parse user input
        # * supported formats:
        #     <amount> [[from_cur][( to | in |:)to_cur]]
        if user_input:
            user_input = user_input.lstrip()
            query['terms'] = user_input.rstrip()

            symbolRegex = r'[a-zA-Z]{3}(,\s*[a-zA-Z]{3})*'

            m = re.match(
                (r"^(?P<amount>\d*([,.]\d+)?)?\s*" +
                    r"(?P<from_cur>" + symbolRegex + ")?\s*" +
                    r"(( to | in |:)\s*(?P<to_cur>" + symbolRegex +"))?$"),
                user_input)

            if m:
                if m.group("from_cur") or m.group("to_cur"):
                    from_cur = self._match_cur_code(m.group("from_cur"))
                    to_cur = self._match_cur_code(m.group("to_cur"))
                    if from_cur:
                        query['from_cur'] = from_cur
                    if to_cur:
                        query['to_cur'] = to_cur
                if m.group("amount"):
                    query['amount'] = float(m.group("amount").rstrip().replace(',', '.'))
        return query

    def _match_cur_code(self, codes):
        if not codes:
            return []
        lst = [x.strip() for x in codes.split(',')]
        return [x.upper() for x in lst if x.upper() in self.currencies]

    def _build_api_url(self, from_cur, to_cur, amount):
        url = self.API_URL + '?'
        url = url + 'q=' + urllib.parse.quote('select * from yahoo.finance.xchange where pair in (')
        pairs = []
        for source in from_cur:
            for out in to_cur:
                pairs.append(urllib.parse.quote('"' + source + out + '"'))
        url = url + ','.join(pairs)
        url = url + urllib.parse.quote(')') + '&'
        url = url + 'format=json' + '&'
        url = url + 'env=' + urllib.parse.quote('store://datatables.org/alltableswithkeys')
        return url

    def _parse_api_response(self, response, query):
        json_root = json.loads(response)
        isList = json_root['query']['count'] != 1
        results = json_root['query']['results']['rate']
        if not isList:
            results = [results]
        ret = []
        for result in results:
            amount = float(result['Rate']) * query['amount']

            source, dest = result['Name'].split('/')
            ret.append(('{0:.8f}'.format(amount).rstrip('0').rstrip('.') + ' ' + dest, source, dest))

        return ret

    def _create_translate_item(self, label):

        def joinCur(lst):
            if len(lst) == 1:
                return lst[0]
            else:
                return ', '.join(lst[:-1]) + ' and ' + lst[-1]

        desc = 'Convert from {} to {}'.format(joinCur(self.default_cur_in), joinCur(self.default_cur_out))

        return self.create_item(
            category=self.ITEMCAT_CONVERT,
            label=label,
            short_desc=desc,
            target="convertcurrency",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS)

    def _create_result_item(self, label, short_desc, target):
        return self.create_item(
            category=self.ITEMCAT_RESULT,
            label=label,
            short_desc=short_desc,
            target=target,
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS,
            data_bag=label)

    def _read_config(self):
        def _warn_cur_code(name, fallback):
            fmt = (
                "Invalid {} value in config. " +
                "Falling back to default: {}")
            self.warn(fmt.format(name, fallback))

        settings = self.load_settings()

        # [default_item]
        self.default_item_enabled = settings.get_bool(
            "enable",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_ITEM_ENABLED)
        self.default_item_label = settings.get_stripped(
            "item_label",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_ITEM_LABEL)

        # default input currency
        input_code = settings.get_stripped(
            "input_cur",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_CUR_IN)
        validated_input_code = self._match_cur_code(input_code)

        if validated_input_code is []:
            _warn_cur_code("input_cur", self.DEFAULT_CUR_IN)
            self.default_cur_in = self.DEFAULT_CUR_IN
        else:
            self.default_cur_in = validated_input_code

        # default output currency
        output_code = settings.get_stripped(
            "output_cur",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_CUR_OUT)
        validated_output_code = self._match_cur_code(output_code)

        if validated_output_code is None:
            _warn_cur_code("output_cur", self.DEFAULT_CUR_OUT)
            self.default_cur_out = self.DEFAULT_CUR_OUT
        else:
            self.default_cur_out = validated_output_code
