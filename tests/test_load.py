from pyiso import client_factory, BALANCING_AUTHORITIES
from pyiso.base import BaseClient
from pyiso.eu import EUClient
from unittest import TestCase
from datetime import datetime, timedelta
import unittest
import pytz
import mock
import libfaketime
import time
import random
libfaketime.reexec_if_needed()


class TestBaseLoad(TestCase):
    def setUp(self):
        # set up expected values from base client
        bc = BaseClient()
        self.MARKET_CHOICES = bc.MARKET_CHOICES
        self.FREQUENCY_CHOICES = bc.FREQUENCY_CHOICES

        # set up other expected values
        self.BA_CHOICES = BALANCING_AUTHORITIES.keys()

    def _run_test(self, ba_name, expect_data=True, tol_min=0, **kwargs):
        # set up
        c = client_factory(ba_name)
        # get data
        data = c.get_load(**kwargs)

        # test number
        if expect_data:
            self.assertGreaterEqual(len(data), 1)
        else:
            self.assertEqual(data, [])

        # test contents
        for dp in data:
            # test key names
            self.assertEqual(set(['load_MW', 'ba_name',
                                  'timestamp', 'freq', 'market']),
                             set(dp.keys()))

            # test values
            self.assertEqual(dp['timestamp'].tzinfo, pytz.utc)
            self.assertIn(dp['ba_name'], self.BA_CHOICES)

            # test for numeric gen
            self.assertGreaterEqual(dp['load_MW']+1, dp['load_MW'])

            # test correct temporal relationship to now
            if c.options['forecast']:
                self.assertGreaterEqual(dp['timestamp'],
                                        pytz.utc.localize(datetime.utcnow())-timedelta(minutes=tol_min))
            else:
                self.assertLess(dp['timestamp'], pytz.utc.localize(datetime.utcnow()))

            # test within date range
            start_at = c.options.get('start_at', False)
            end_at = c.options.get('end_at', False)
            if start_at and end_at:
                self.assertGreaterEqual(dp['timestamp'], start_at)
                self.assertLessEqual(dp['timestamp'], end_at)

        # return
        return data

    def _run_notimplemented_test(self, ba_name, **kwargs):
        # set up
        c = client_factory(ba_name)

        # method not implemented yet
        self.assertRaises(NotImplementedError, c.get_load)

    def _run_null_repsonse_test(self, ba_name, **kwargs):
        # set up
        c = client_factory(ba_name)

        # mock request
        with mock.patch.object(c, 'request') as mock_request:
            mock_request.return_value = None

            # get data
            data = c.get_load(**kwargs)

            # test
            self.assertEqual(data, [])


class TestBPALoad(TestBaseLoad):
    def test_null_response_latest(self):
        self._run_null_repsonse_test('BPA', latest=True)

    def test_latest(self):
        # basic test
        data = self._run_test('BPA', latest=True, market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('BPA', start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1))

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_date_range_strings(self):
        # basic test
        self._run_test('BPA', start_at='2016-05-01', end_at='2016-05-03')

    def test_date_range_farpast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('BPA', start_at=today-timedelta(days=20),
                              end_at=today-timedelta(days=10))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)


class TestCAISOLoad(TestBaseLoad):
    def test_null_response_latest(self):
        self._run_null_repsonse_test('CAISO', latest=True)

    def test_latest(self):
        # basic test
        data = self._run_test('CAISO', latest=True, market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('CAISO', start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1),
                              tol_min=1)

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_date_range_strings(self):
        # basic test
        self._run_test('CAISO', start_at='2016-05-01', end_at='2016-05-03')

#     @freezegun.freeze_time('2015-05-20 14:30', tz_offset=0, tick=True)
#     @requests_mock.mock()
#     def test_forecast(self, mocker):
#         url = 'http://oasis.caiso.com/oasisapi/SingleZip'
#         with open('responses/SLD_FCST.zip', 'rb') as ffile:
#             mocker.get(url, content=ffile.read())
#
    def test_forecast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('CAISO', start_at=today+timedelta(hours=4),
                              end_at=today+timedelta(days=2),
                              tol_min=4*60)

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)


class TestERCOTLoad(TestBaseLoad):
    def test_null_response_latest(self):
        self._run_null_repsonse_test('ERCOT', latest=True)

    def test_null_response_forecast(self):
        today = datetime.today().replace(tzinfo=pytz.utc)
        self._run_null_repsonse_test('ERCOT', start_at=today + timedelta(hours=20),
                                     end_at=today+timedelta(days=2))

    def test_latest(self):
        # basic test
        data = self._run_test('ERCOT', latest=True, market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_forecast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('ERCOT', start_at=today + timedelta(hours=20),
                              end_at=today+timedelta(days=2))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test timestamps in range
        self.assertGreaterEqual(min(timestamps), today+timedelta(hours=20))
        self.assertLessEqual(min(timestamps), today+timedelta(days=2))


class TestISONELoad(TestBaseLoad):
    def test_null_response_latest(self):
        self._run_null_repsonse_test('ISONE', latest=True)

    def test_latest(self):
        # basic test
        data = self._run_test('ISONE', latest=True)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('ISONE', start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_date_range_strings(self):
        # basic test
        self._run_test('ISONE', start_at='2016-05-01', end_at='2016-05-03')

    def test_forecast(self):
        # basic test
        data = self._run_test('ISONE', forecast=True, market='DAHR', freq='1hr')

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)


class TestMISOLoad(TestBaseLoad):
    def test_null_response_forecast(self):
        today = pytz.utc.localize(datetime.utcnow())
        self._run_null_repsonse_test('MISO', start_at=today + timedelta(hours=2),
                                     end_at=today+timedelta(days=2))

    def test_forecast(self):
        # basic test
        today = pytz.utc.localize(datetime.utcnow())
        data = self._run_test('MISO', start_at=today + timedelta(hours=2),
                              end_at=today+timedelta(days=2))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test timestamps in range
        self.assertGreaterEqual(min(timestamps), today+timedelta(hours=2))
        self.assertLessEqual(min(timestamps), today+timedelta(days=2))


class TestNEVPLoad(TestBaseLoad):
    def test_null_response_latest(self):
        self._run_null_repsonse_test('NEVP', latest=True)

    def test_latest(self):
        # basic test
        data = self._run_test('NEVP', latest=True)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.hourly)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)

    def test_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('NEVP', start_at=today-timedelta(days=1),
                              end_at=today)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_date_range_strings(self):
        # basic test
        self._run_test('NEVP', start_at='2016-05-01', end_at='2016-05-03')

#     @libfaketime.fake_time('2016-05-20 14:45')
#     @requests_mock.mock()
#     def test_date_range_farpast(self, mocker):
#         url = ('http://www.oasis.oati.com/NEVP/NEVPdocs/inetloading/'
#                'Monthly_Ties_and_Loads_L_from_04_01_2016_to_04_30_2016_.html')
#         with open('responses/NEVP_load_farpast.htm', 'r') as ffile:
#             mocker.get(url, content=ffile.read())
#
    def test_date_range_farpast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('NEVP', start_at=today-timedelta(days=35),
                              end_at=today-timedelta(days=33))
        self.assertEqual(len(data), 2*24)


class TestNYISOLoad(TestBaseLoad):
    def test_null_response_latest(self):
        self._run_null_repsonse_test('NYISO', latest=True)

    def test_latest(self):
        # basic test
        data = self._run_test('NYISO', latest=True, market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('NYISO', start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_date_range_strings(self):
        # basic test
        self._run_test('NYISO', start_at='2016-05-01', end_at='2016-05-03')

    def test_forecast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('NYISO', start_at=today + timedelta(hours=20),
                              end_at=today+timedelta(days=2))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test timestamps in range
        self.assertGreaterEqual(min(timestamps), today+timedelta(hours=20))
        self.assertLessEqual(min(timestamps), today+timedelta(days=2))


class TestPJMLoad(TestBaseLoad):
    def test_null_response_latest(self):
        self._run_null_repsonse_test('PJM', latest=True)

    def test_latest(self):
        # basic test
        data = self._run_test('PJM', latest=True, market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_forecast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('PJM', start_at=today + timedelta(hours=20),
                              end_at=today+timedelta(days=2))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test timestamps in range
        self.assertGreaterEqual(min(timestamps), today+timedelta(hours=20))
        self.assertLessEqual(min(timestamps), today+timedelta(days=2))

    def test_historical(self):
        start_at = datetime(2015, 1, 2, 0, tzinfo=pytz.utc)
        end_at = datetime(2015, 12, 31, 23, tzinfo=pytz.utc)
        data = self._run_test('PJM', start_at=start_at, end_at=end_at)

        timestamps = [d['timestamp'] for d in data]

        # 364 days, except for DST transition hours
        # TODO handle DST transitions instead of dropping them
        self.assertEqual(len(set(timestamps)), 364*24-2)

    def test_date_range_strings(self):
        data = self._run_test('PJM', start_at='2016-06-10', end_at='2016-06-11')

        timestamps = [d['timestamp'] for d in data]

        # 3 days plus 1 hr
        self.assertEqual(len(set(timestamps)), 24 + 1)


class TestSPPLoad(TestBaseLoad):
    def test_failing(self):
        self._run_notimplemented_test('SPP')


class TestSPPCLoad(TestBaseLoad):
    def test_null_response(self):
        self._run_null_repsonse_test('SPPC', latest=True)

    def test_latest(self):
        # basic test
        data = self._run_test('SPPC', latest=True)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.hourly)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)

    def test_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('SPPC', start_at=today-timedelta(days=1),
                              end_at=today)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

#     @freezegun.freeze_time('2015-05-20 11:30', tz_offset=0, tick=True)
#     @requests_mock.mock()
#     def test_date_range_farpast(self, mocker):
#         url = ('http://www.oasis.oati.com/NEVP/NEVPdocs/inetloading/'
#                'Monthly_Ties_and_Loads_L_from_04_01_2015_to_04_30_2015_.html')
#         with open('responses/SPPC_load_farpast.htm', 'r') as ffile:
#             mocker.get(url, content=ffile.read())
    def test_date_range_farpast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('SPPC', start_at=today-timedelta(days=35),
                              end_at=today-timedelta(days=33))

    def test_date_range_strings(self):
        # basic test
        self._run_test('SPPC', start_at='2016-05-01', end_at='2016-05-03')


class TestSVERILoad(TestBaseLoad):
    def setUp(self):
        super(TestSVERILoad, self).setUp()
        self.bas = [k for k, v in BALANCING_AUTHORITIES.items() if v['module'] == 'sveri']

    def test_null_response(self):
        self._run_null_repsonse_test(self.bas[0], latest=True)

    def test_latest_all(self):
        for ba in self.bas:
            self._test_latest(ba)

    def test_date_range_all(self):
        for ba in self.bas:
            self._test_date_range(ba)

    def _test_latest(self, ba):
        # basic test
        data = self._run_test(ba, latest=True)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def _test_date_range(self, ba):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test(ba, start_at=today - timedelta(days=3),
                              end_at=today - timedelta(days=2), market=self.MARKET_CHOICES.fivemin)

        # test timestamps are different
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)


@unittest.skip('Not ready')
class TestEULoad(TestBaseLoad):
    def setUp(self):
        super(TestEULoad, self).setUp()
        self.BA_CHOICES = EUClient.CONTROL_AREAS.keys()

    def test_latest(self):
        # basic test
        data = self._run_test('EU', latest=True, market=self.MARKET_CHOICES.hourly,
                              control_area='IT')

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.hourly)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)

    def test_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('EU', start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1),
                              control_area='IT')

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_forecast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('EU', start_at=today+timedelta(hours=20),
                              end_at=today+timedelta(days=1),
                              control_area='IT')

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)


class TestEIALoad(TestBaseLoad):

    def setUp(self):
        super(TestEIALoad, self).setUp()
        self.BA_CHOICES = [k for k, v in BALANCING_AUTHORITIES.items() if v['module'] == 'eia_esod']
        self.can_mex = ['IESO', 'BCTC', 'MHEB', 'AESO', 'HQT', 'NBSO', 'CFE',
                        'SPC']
        self.us_bas = [i for i in self.BA_CHOICES if i not in self.can_mex]
        no_load = ['DEAA-EIA', 'EEI', 'GRIF-EIA', 'GRMA', 'GWA',
                   'HGMA-EIA', 'SEPA', 'WWA', 'YAD']
        delay_bas = ['AEC', 'DOPD', 'GVL', 'HST', 'NSB', 'PGE', 'SCL',
                     'TAL', 'TIDC', 'TPWR']
        self.load_bas = [i for i in self.us_bas if i not in no_load]
        self.no_delay_load_bas = [i for i in self.load_bas if i not in delay_bas]
        self.problem_bas = ['GRID']

    def test_null_response(self):
        self._run_null_repsonse_test(self.load_bas[0], latest=True)

    def test_null_response_latest(self):
        self._run_null_repsonse_test(self.load_bas[0], latest=True)

    def test_null_response_forecast(self):
        today = datetime.today().replace(tzinfo=pytz.utc)
        self._run_null_repsonse_test(self.load_bas[0],
                                     start_at=today + timedelta(hours=20),
                                     end_at=today+timedelta(days=2))

    # def test_latest_some(self):
    #     # Test 5 BAs to stop getting throttled
    #     for ba in random.sample(self.bas, 5):
    #         self._test_latest(ba)
    #         time.sleep(5)  # Delay to cut down on throttling

    # fix this one
    def test_latest_all(self):
        for ba in self.load_bas:
            self._test_latest(ba)

    # def test_date_range_some(self):
    #     for ba in random.sample(self.bas, 5):
    #         self._test_date_range(ba)
    #         time.sleep(5)  # Delay to cut down on throttling

    # fix this
    def test_date_range_all(self):
        for ba in self.load_bas:
            if ba in self.problem_bas:
                continue
            self._test_date_range(ba)

    # def test_date_range_strings_some(self):
    #     for ba in random.sample(self.bas, 5):
    #         # basic test
    #         self._run_test(ba, start_at='2016-05-01', end_at='2016-05-03')

    def test_date_range_strings_all(self):
        for ba in self.load_bas:
            # basic test
            if ba in self.problem_bas:
                continue
            self._run_test(ba, start_at='2016-05-01', end_at='2016-05-03')

    # def test_date_range_farpast_some(self):
    #     for ba in random.sample(self.bas, 5):
    #         # basic test
    #         today = datetime.today().replace(tzinfo=pytz.utc)
    #         data = self._run_test(ba, start_at=today-timedelta(days=20),
    #                               end_at=today-timedelta(days=10))
    #
    #         # test timestamps are not equal
    #         timestamps = [d['timestamp'] for d in data]
    #         self.assertGreater(len(set(timestamps)), 1)

    def test_date_range_farpast_all(self):
        for ba in self.load_bas:
            if ba in self.problem_bas:
                continue
            # basic test
            today = datetime.today().replace(tzinfo=pytz.utc)
            data = self._run_test(ba, start_at=today-timedelta(days=20),
                                  end_at=today-timedelta(days=10))

            # test timestamps are not equal
            timestamps = [d['timestamp'] for d in data]
            self.assertGreater(len(set(timestamps)), 1)

    # def test_date_range_all(self):
    #     for ba in self.bas:
    #         self._test_date_range(ba)
    #         time.sleep(30)  # Delay to cut down on throttling

    # def test_forecast_some(self):
    #     delay_bas = ['AEC', 'DOPD', 'GVL', 'HST', 'NSB', 'PGE', 'SCL',
    #                  'TAL', 'TIDC', 'TPWR']
    #     no_delay_bas = [i for i in self.bas if i not in delay_bas]
    #     for ba in random.sample(no_delay_bas, 5):
    #         self._test_forecast(ba)
    #         time.sleep(5)  # Delay to cut down on throttling

    # fix this one
    def test_forecast_all(self):
        for ba in self.no_delay_load_bas:
            if ba == "SEC":
                continue
            self._test_forecast(ba)
            # time.sleep(30)  # Delay to cut down on throttling

    # this one probably should move to eia_esod
    def test_all_us_bas(self):
        for ba in self.us_bas:
            data = self._run_test(ba, market=self.MARKET_CHOICES.hourly)
            self.assertGreater(len(data), 1)

    def test_non_us_bas_raise_valueerror(self):
        for ba in self.can_mex:
            with self.assertRaises(ValueError):
                self._run_test(ba, market=self.MARKET_CHOICES.hourly)

    def _test_forecast(self, ba):
        # Used 5 hours/1 day insetad of 20/2 for one day forecast
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test(ba, start_at=today + timedelta(hours=5),
                              end_at=today+timedelta(days=1))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test timestamps in range
        self.assertGreaterEqual(min(timestamps), today+timedelta(hours=5))
        self.assertLessEqual(min(timestamps), today+timedelta(days=1))

    def _test_latest(self, ba):
        # basic test
        data = self._run_test(ba, latest=True)
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.hourly)
            # hourly='RTHR'
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)

    def _test_date_range(self, ba):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test(ba, start_at=today - timedelta(days=3),
                              end_at=today - timedelta(days=2),
                              market=self.MARKET_CHOICES.hourly)

        # test timestamps are different
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.hourly)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)
