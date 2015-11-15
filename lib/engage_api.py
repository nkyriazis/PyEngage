__author__ = "Nikolaos Kyriazis"
__copyright__ = "Copyright 2015 Nikolaos Kyriazis"
__license__ = "APACHE"
__version__ = "2.0"

import datetime
import json
from itertools import izip
from urllib import urlencode
from urllib2 import Request, urlopen

import numpy as np


def json_get_url(req):
    """ Issue a get request and deserialize json response.
    :param req: the url containing the request.
    :return: The json response, parsed into a dictionary.
    """
    request = Request(req)
    return json.loads(urlopen(request).read())


def json_get_url_params(url, params):
    """ Issue a get request and encode parameters in it.
    :param url: The base url request.
    :param params: The python parameters to be encoded in the url.
    :return: The json response, parsed into a dictionary.
    """
    req = url + '?' + urlencode(params)
    return json_get_url(req)


def merge_dicts(d1, d2):
    """ Merges two dictionaries
    :param d1: First dictionary.
    :param d2: Second dictionary.
    :return: A dictionary initialized after d1 and updated over d2.
    """
    ret = d1.copy()
    ret.update(d2)
    return ret


def efergy_ts_to_datetime(efergyTS):
    """ Decodes an efergy timestamp.

    The efergy platform stores and provides timestamps in
    amount of seconds from 1/1/1970 00:00, UTC. This method
    reconstructs a python datetime object from such a timestamp.

    :param efergyTS: The efergy timestamp.
    :return: A datetime object.
    """
    return datetime.datetime.utcfromtimestamp(efergyTS / 1000.0)


def datetime_to_efergy_ts(datetime):
    """ Encodes a datetime object into an efergy timestamp.

    Efergy expects timestamp parameters as the amount of seconds
    from 1/1/1970 00:00, UTC.

    :param datetime: A datetime object.
    :return: A timestamp that can be used in the efergy queries.
    """
    return (datetime - efergy_ts_to_datetime(0)).total_seconds()


class EngageLink(object):
    """ A link to the efergy platform.

    The link is a lightweight pythonization of the
    web api of the efergy platform. It is initlialized
    through some basic authentication, using credentials
    or a provided token. It provides a basic api that
    queries the efergy platform for energy consumption data.
    """

    # The initialization api url base.
    base = 'https://engage.efergy.com/mobile/'

    # The query api url base.
    base_proxy = 'https://engage.efergy.com/mobile_proxy/'

    def __init__(self, token=None, username=None, password=None):
        """ Construct a new link.

        A link is initialized with either a pre-acquired token
        or credentials that would lead to acquiring a token.

        :param token: A pre-acquired token. Such tokens can be acquired through the efergy platform.
        :param username: Username or e-mail for logging into the efergy platform.
        :param password: Password for logging into the efergy platform.
        :return: A new link.
        """
        if token is not None:
            self.token = token
        elif username is not None and password is not None:
            self.token = json_get_url_params(self.base + 'get_token',
                                             {'username': username, 'password': password, 'device': 'android'})['token']
        else:
            raise RuntimeError('need to specify either token or username and password')

    def call(self, method, **params):
        """ Web-api calling helper.
        :param method: The method's name.
        :param params: The parameters to be passed
        :return: The json-parsed result.
        """
        return json_get_url_params(self.base_proxy + method, merge_dicts({'token': self.token}, params))

    def getInstant(self):
        """ Get live info.
        :return: A tuple containing
                    a) the last sensor reading (consumption watts), in kWs,
                    b) the age of the reading in seconds,
                    c) the timestamp of the last reading.
        """
        result = self.call('getInstant')
        return result['reading'] / 1000.0, result['age'], efergy_ts_to_datetime(result['last_reading_time'])

    def getMontlyBudget(self):
        """ Cost info.
        :return: The ctarget budget, as configures by the user. No currency attached.
        """
        return self.call('getBudget')['monthly_budget']

    def getCost(self, zoneOffset=+2, period='custom',
                fromTime=datetime.datetime.now() - datetime.timedelta(days=1),
                toTime=datetime.datetime.now()):
        """ Computer cost for a given period of time.
        :param zoneOffset: GMT offset.
        :param period: Any of 'minute', '15minute', '30minute', 'hour', 'day', 'week', 'month', 'year'
        :param fromTime: A starting timestamp datetime.
        :param toTime: An ending timestamp datetime.
        :return: The cost computed for the provided period. No currency attached.
        """
        result = self.call('getCost', offset=-zoneOffset * 60,
                           fromTime=datetime_to_efergy_ts(fromTime),
                           toTime=datetime_to_efergy_ts(toTime))
        return result['sum'], result['units']

    def getTimeSeries(self, offset=+2,
                      fromTime=datetime.datetime.now() - datetime.timedelta(days=1),
                      toTime=datetime.datetime.now(),
                      aggPeriod='minute', aggFunc='avg'):
        """ Get a time series of energy consumption.
        :param offset: GMT offset.
        :param fromTime: A starting timestamp datetime.
        :param toTime: An ending timestamp datetime.
        :param aggPeriod: Any of 'minute', '15minute', '30minute', 'hour', 'day', 'week', 'month', 'year'
        :param aggFunc: Any of 'avg', 'sum'
        :return: A list of pairs, with each pair comprising a datetime and a measurement in kWs.
        """
        results = self.call('getTimeSeries',
                            offset=-60 * offset,
                            fromTime=datetime_to_efergy_ts(fromTime),
                            toTime=datetime_to_efergy_ts(toTime),
                            aggPeriod=aggPeriod,
                            aggFunc=aggFunc)
        return self.parseResults(results)

    def parseResults(self, results):
        """ Helper function to put sense into timeseries data provided by the efergy platform.
        :param results: A json timeseries.
        :return: A list of pairs of datetimes and measurements in kWs.
        """

        def getNumber(v):
            try:
                return float(v)
            except:
                return 0

        return sorted(
            [(efergy_ts_to_datetime(int(key)), getNumber(val[0])) for key, val in results['data'].iteritems()])

    def makeTimeSeriesQuery(self, getter):
        """ Helper function to execute standard time series queries.
        :param getter: The query method name.
        :return: :return: A list of pairs, with each pair comprising a datetime and a measurement in kWs.
        """
        results = self.call(getter)
        return self.parseResults(results)

    def getDay(self):
        """ Day query.
        :return: Per minute consumption for the last day.
        """
        return self.makeTimeSeriesQuery('getDay')

    def getWeek(self):
        """ Week query
        :return: Per day consumption for the last week.
        """
        return self.makeTimeSeriesQuery('getWeek')

    def getMonth(self):
        """ Month query
        :return: Per day consumption for the last 28 days of the month.
        """
        return self.makeTimeSeriesQuery('getMonth')

    def getYear(self):
        """ Year query
        :return: Per month consumption for the last year.
        """
        return self.makeTimeSeriesQuery('getYear')

    def getImageDate(self, imgFilename):
        """ Helper function to extract data from image file meta-data.
        :param imgFilename: The path to the image.
        :return: The stored datetime.
        """
        from PIL import Image
        TSTAG = 36867
        img = Image.open(imgFilename)
        exif = img._getexif()
        return datetime.datetime.strptime(exif[TSTAG][0], '%Y:%m:%d %H:%M:%S')

    def getTimeSeriesBetweenImages(self, img1, img2, offset=2):
        """ Get the consumption curve for a period marked by two images.
        :param img1: Path to the early date image.
        :param img2: Path to the late date image.
        :param offset: GMT offset
        :return: Per minute consumption.
        """
        return self.getTimeSeries(offset=offset,
                                  fromTime=self.getImageDate(img1),
                                  toTime=self.getImageDate(img2))

    def integrateTimeSeries(self, timeSeries):
        """ Compute the amount of kWhs in a time series
        :param timeSeries: The time series to integrate
        :return: The total amount of kWhs
        """

        def trivialTimeMapping(dt): return 0

        return self.integrateTimeSeriesMulti(timeSeries, trivialTimeMapping)[0]

    def integrateTimeSeriesMulti(self, timeSeries, timeMapping):
        """ Compute the amount of kWhs in a tiem series, split in timezones
        :param timeSeries: The time series to integrate.
        :param timeMapping: A function which maps a datetime to a category id.
        :return: A dictionary of datetime mappings and kWhs integrals.
        """
        timestamps = np.array([ts[0] for ts in timeSeries])
        dt = (timestamps[1] - timestamps[0]).total_seconds()
        kwhs = np.array([ts[1] for ts in timeSeries])

        ret = {}

        for t, v in izip(timestamps, kwhs):
            key = timeMapping(t)
            if key in ret:
                sum = ret[key]
            else:
                sum = 0
            sum += v
            ret[key] = sum

        for key in ret:
            ret[key] *= dt / 3600

        return ret

    def computeCost(self, timeSeries, timeDependentKwhTariffFunc):
        """ Computes a time series cost, according to some tariff mapping.
        :param timeSeries: The time series to compute cost upon.
        :param timeDependentKwhTariffFunc: The time tariff mapping.
        :return: Total cost
        """
        kwhs = self.integrateTimeSeriesMulti(timeSeries, timeDependentKwhTariffFunc)
        ret = 0
        for key, val in kwhs.iteritems():
            ret += key * val
        return ret
