from pyiso import client_factory, BALANCING_AUTHORITIES
from pyiso.base import BaseClient
from unittest import TestCase
import pytz
from datetime import datetime, timedelta
import sys
from nose_parameterized import parameterized


class TestBaseLMP(TestCase):
    def setUp(self):
        # set up expected values from base client
        bc = BaseClient()
        self.MARKET_CHOICES = bc.MARKET_CHOICES
        self.FREQUENCY_CHOICES = bc.FREQUENCY_CHOICES

        # set up other expected values
        self.BA_CHOICES = BALANCING_AUTHORITIES.keys()

    def _run_test(self, ba_name, expect_data=True, tol_min=8, **kwargs):
        # set up
        c = client_factory(ba_name)

        # get data
        data = c.get_lmp(**kwargs)

        # test number
        if expect_data:
            self.assertGreaterEqual(len(data), 1)
        else:
            self.assertEqual(data, [])

        # test contents
        for dp in data:
            # test key names
            self.assertEqual(set(['lmp', 'ba_name',
                                  'timestamp', 'market', 'node_id', 'lmp_type', 'freq']),
                             set(dp.keys()))

            # test values
            self.assertEqual(dp['timestamp'].tzinfo, pytz.utc)
            self.assertIn(dp['ba_name'], self.BA_CHOICES)

            # test for numeric price
            self.assertGreaterEqual(dp['lmp']+1, dp['lmp'])

            # test correct temporal relationship to now
            now = pytz.utc.localize(datetime.utcnow())
            if c.options['forecast']:
                self.assertGreaterEqual(dp['timestamp'], now)
            elif c.options['latest']:
                # within 8 min
                delta = now - dp['timestamp']
                self.assertLess(abs(delta.total_seconds()), tol_min*60)
            else:
                self.assertLess(dp['timestamp'], now)

        # return
        return data

    def _run_notimplemented_test(self, ba_name, **kwargs):
        # set up
        c = client_factory(ba_name)

        # method not implemented yet
        self.assertRaises(NotImplementedError, c.get_lmp)


class TestCAISOLMP(TestBaseLMP):
    def test_latest(self):
        # basic test
        data = self._run_test('CAISO', node_id='SLAP_PGP2-APND',
                              latest=True, market=self.MARKET_CHOICES.fivemin)

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
        data = self._run_test('CAISO', node_id='SLAP_PGP2-APND',
                              start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_forecast(self):
        # basic test
        now = pytz.utc.localize(datetime.utcnow())
        data = self._run_test('CAISO', node_id='SLAP_PGP2-APND',
                              start_at=now+timedelta(hours=20),
                              end_at=now+timedelta(days=2),
                              market=self.MARKET_CHOICES.dam)

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_bad_node(self):
        self._run_test('CAISO', node_id='badnode', expect_data=False, latest=True)


class TestISONELMP(TestBaseLMP):
    def test_latest(self):
        # basic test
        data = self._run_test('ISONE', node_id='NEMASSBost',
                              latest=True, market=self.MARKET_CHOICES.fivemin)

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
        data = self._run_test('ISONE', node_id='NEMASSBost',
                              start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)


class TestNYISOLMP(TestBaseLMP):
    def test_latest(self):
        # basic test
        data = self._run_test('NYISO', node_id=None,
                              latest=True, market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_forecast(self):
        # basic test
        now = pytz.utc.localize(datetime.utcnow())
        data = self._run_test('NYISO', node_id='LONGIL',
                              start_at=now, end_at=now+timedelta(days=1))

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.dam)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)

    def test_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('NYISO', node_id='LONGIL',
                              start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)


class TestPJMLMP(TestBaseLMP):
    def test_latest(self):
        # basic test
        data = self._run_test('PJM', node_id='COMED',
                              market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_latest_oasis(self):
        data = self._run_test('PJM', node_id=None, tol_min=10,
                              market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def forecast(self):  # skip
        # basic test
        now = pytz.utc.localize(datetime.utcnow())
        data = self._run_test('PJM', node_id=33092371,
                              start_at=now, end_at=now+timedelta(days=1))

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.dam)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)

    def test_date_range_dayahead_hourly(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('PJM', node_id=33092371,
                              start_at=today-timedelta(days=2),
                              end_at=today-timedelta(hours=40))

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_date_range_realtime_hourly(self):
         # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('PJM', node_id=33092371,
                              start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1),
                              market=self.MARKET_CHOICES.hourly)

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_multiple_lmp_realtime(self):
        node_list = ['AECO', 'AEP', 'APS', 'ATSI', 'BGE', 'COMED', 'DAY', 'DAY',
                     'DOM', 'DPL', 'DUQ', 'EKPC', 'JCPL', 'METED', 'PECO', 'PENELEC',
                     'PEPCO', 'PPL', 'PSEG', 'RECO']
        data = self._run_test('PJM', tol_min=10, node_id=node_list, latest=True,
                              market=self.MARKET_CHOICES.fivemin)

        nodes_returned = [d['node_id'] for d in data]
        for node in nodes_returned:
            self.assertIn(node, nodes_returned)

    def test_multiple_lmp_realtime_mixed(self):
        node_list = ['AECO', 'AEP', 'APS', 'ATSI', 'BGE', 'COMED', 'DAY', 'DAY',
                     'DOM', 'DPL', 'DUQ', 'EKPC', 'JCPL', 'METED', 'PECO', 'PENELEC',
                     'PEPCO', 'PPL', 'PSEG', 'RECO', '33092371']
        data = self._run_test('PJM', tol_min=10, node_id=node_list, latest=True,
                              market=self.MARKET_CHOICES.fivemin)

        nodes_returned = [d['node_id'] for d in data]
        for node in nodes_returned:
            self.assertIn(node, nodes_returned)

    def test_multiple_lmp_realtime_oasis(self):
        node_list = ['MERIDIAN EWHITLEY', 'LANSDALE']
        data = self._run_test('PJM', tol_min=10, node_id=node_list, latest=True,
                              market=self.MARKET_CHOICES.fivemin)

        nodes_returned = [d['node_id'] for d in data]
        for node in nodes_returned:
            self.assertIn(node, nodes_returned)


class TestMISOLMP(TestBaseLMP):
    def test_latest(self):
        # basic test
        data = self._run_test('MISO', node_id=None,
                              market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def forecast(self):  # skip
        # basic test
        now = pytz.utc.localize(datetime.utcnow())
        data = self._run_test('MISO', node_id=None,
                              start_at=now, end_at=now+timedelta(days=1))

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.dam)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)


class TestERCOTLMP(TestBaseLMP):
    def test_latest(self):
        # basic test
        data = self._run_test('ERCOT', latest=True,
                              market=self.MARKET_CHOICES.fivemin)

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.fivemin)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.fivemin)

    def test_latest_single_node(self):
        data = self._run_test('ERCOT', node_id='HB_HOUSTON', latest=True,
                              market=self.MARKET_CHOICES.fivemin)

        self.assertEqual(len(data), 1)

    def test_latest_multi_node(self):
        data = self._run_test('ERCOT', node_id=['LZ_HOUSTON', 'LZ_NORTH'], latest=True,
                              market=self.MARKET_CHOICES.fivemin)

        self.assertEqual(len(data), 2)

    def test_date_range_dayahead_hourly(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('ERCOT', node_id=['LZ_HOUSTON', 'LZ_NORTH'],
                              start_at=today-timedelta(days=2),
                              end_at=today-timedelta(hours=40),
                              market=self.MARKET_CHOICES.dam)

        # test timestamps are not equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_forecast(self):
        # basic test
        now = pytz.utc.localize(datetime.utcnow())
        data = self._run_test('ERCOT', node_id=['LZ_HOUSTON', 'LZ_NORTH'],
                              start_at=now, end_at=now+timedelta(days=1))

        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

        # test flags
        for dp in data:
            self.assertEqual(dp['market'], self.MARKET_CHOICES.dam)
            self.assertEqual(dp['freq'], self.FREQUENCY_CHOICES.hourly)


#####################################################################
# Test minumum LMP functions, test-runner cannot run individual tests
# with parameterized.expand, so separate out into classes

class TestLatestLMP(TestBaseLMP):
    @parameterized.expand([
        ('CAISO', 'CAISO', True),
        ('MISO', 'MISO', True),
        ('ERCOT', 'ERCOT', True),
        ('NYISO', 'NYISO', True),
        ('ISONE', 'ISONE', True),
    ])
    def test_latest(self, name, ba, expected):
        data = self._run_test(ba, latest=True,
                              market=self.MARKET_CHOICES.fivemin)
        self.assertEqual(len(set([t['timestamp'] for t in data])), 1)


class TestForecastLMP(TestBaseLMP):
    @parameterized.expand([
        ('CAISO', 'CAISO', True),
        ('MISO', 'MISO', True),
        ('ERCOT', 'ERCOT', True),
        ('NYISO', 'NYISO', True),
        ('ISONE', 'ISONE', True),
    ])
    def test_forecast(self, name, ba, expected):
        now = datetime.now(pytz.utc)
        data = self._run_test(ba,  start_at=now, end_at=now + timedelta(days=1),
                              market=self.MARKET_CHOICES.dam)
        self.assertGreater(len(data), 1)


class TestTodayLMP(TestBaseLMP):
    @parameterized.expand([
        ('CAISO', 'CAISO', True),
        ('MISO', 'MISO', True),
        ('ERCOT', 'ERCOT', True),
        ('NYISO', 'NYISO', True),
        ('ISONE', 'ISONE', True),
    ])
    def test_today(self, name, ba, expected):
        now = datetime.now(pytz.utc)
        data = self._run_test(ba,  start_at=now - timedelta(days=1), end_at=now,
                              market=self.MARKET_CHOICES.hourly)
        self.assertGreater(len(data), 1)

