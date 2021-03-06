from unittest import TestCase
from mock import Mock, patch
import elasticsearch
import yaml
import curator
# Get test variables and constants from a single source
from . import testvars as testvars

class TestSnapshotListClientAndInit(TestCase):
    def test_init_bad_client(self):
        client = 'not a real client'
        self.assertRaises(TypeError, curator.SnapshotList, client)
    def test_init_no_repo_exception(self):
        client = Mock()
        self.assertRaises(curator.MissingArgument, curator.SnapshotList, client)
    def test_init_get_snapshots_exception(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get.side_effect = testvars.fake_fail
        client.snapshot.get_repository.return_value = {}
        self.assertRaises(
            curator.FailedExecution,
            curator.SnapshotList, client, repository=testvars.repo_name
        )
    def test_init(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertEqual(testvars.snapshots['snapshots'],sl.all_snapshots)
        self.assertEqual(
            ['snap_name','snapshot-2015.03.01'], sorted(sl.snapshots)
        )

class TestSnapshotListOtherMethods(TestCase):
    def test_empty_list(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertEqual(2, len(sl.snapshots))
        sl.snapshots = []
        self.assertRaises(curator.NoSnapshots, sl.empty_list_check)
    def test_working_list(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertEqual(['snap_name', 'snapshot-2015.03.01'], sl.working_list())

class TestSnapshotListAgeFilterName(TestCase):
    def test_get_name_based_ages_match(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl._get_name_based_ages('%Y.%m.%d')
        self.assertEqual(1425168000,
            sl.snapshot_info['snapshot-2015.03.01']['age_by_name']
        )
    def test_get_name_based_ages_no_match(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl._get_name_based_ages('%Y.%m.%d')
        self.assertIsNone(sl.snapshot_info['snap_name']['age_by_name'])

class TestSnapshotListStateFilter(TestCase):
    def test_success_inclusive(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_state(state='SUCCESS')
        self.assertEqual(
            [u'snap_name', u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
    def test_success_exclusive(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.inprogress
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_state(state='SUCCESS', exclude=True)
        self.assertEqual([u'snapshot-2015.03.01'], sorted(sl.snapshots))
    def test_invalid_state(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertRaises(ValueError, sl.filter_by_state, state='invalid')

class TestSnapshotListRegexFilters(TestCase):
    def test_filter_by_regex_prefix(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertEqual(
            [u'snap_name', u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
        sl.filter_by_regex(kind='prefix', value='sna')
        self.assertEqual(
            [u'snap_name', u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
        sl.filter_by_regex(kind='prefix', value='sna', exclude=True)
        self.assertEqual([], sl.snapshots)
    def test_filter_by_regex_prefix_exclude(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertEqual(
            [u'snap_name', u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
        sl.filter_by_regex(kind='prefix', value='snap_', exclude=True)
        self.assertEqual([u'snapshot-2015.03.01'], sl.snapshots)
    def test_filter_by_regex_timestring(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertEqual(
            [u'snap_name', u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
        sl.filter_by_regex(kind='timestring', value='%Y.%m.%d')
        self.assertEqual(
            [u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
        sl.filter_by_regex(kind='timestring', value='%Y.%m.%d', exclude=True)
        self.assertEqual([], sl.snapshots)
    def test_filter_by_regex_no_value(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertEqual(
            [u'snap_name', u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
        self.assertRaises(ValueError, sl.filter_by_regex, kind='prefix', value=None)
        self.assertEqual(
            [u'snap_name', u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
        sl.filter_by_regex(kind='prefix', value=0)
        self.assertEqual([], sl.snapshots)
    def test_filter_by_regex_bad_kind(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertEqual(
            [u'snap_name', u'snapshot-2015.03.01'],
            sorted(sl.snapshots)
        )
        self.assertRaises(
            ValueError, sl.filter_by_regex, kind='invalid', value=None)

class TestSnapshotListFilterByAge(TestCase):
    def test_filter_by_age_missing_direction(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertRaises(curator.MissingArgument,
            sl.filter_by_age, unit='days', unit_count=1
        )
    def test_filter_by_age_bad_direction(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertRaises(ValueError, sl.filter_by_age, unit='days',
            unit_count=1, direction="invalid"
        )
    def test_filter_by_age_invalid_source(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertRaises(ValueError, sl.filter_by_age, unit='days',
            source='invalid', unit_count=1, direction="older"
        )
    def test_filter_by_age__name_no_timestring(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        self.assertRaises(curator.MissingArgument,
            sl.filter_by_age,
            source='name', unit='days', unit_count=1, direction='older'
        )
    def test_filter_by_age__name_older_than_now(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_age(source='name', direction='older',
            timestring='%Y.%m.%d', unit='days', unit_count=1
        )
        self.assertEqual(['snapshot-2015.03.01'], sl.snapshots)
    def test_filter_by_age__name_younger_than_now(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_age(source='name', direction='younger',
            timestring='%Y.%m.%d', unit='days', unit_count=1
        )
        self.assertEqual([], sl.snapshots)
    def test_filter_by_age__name_younger_than_past_date(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_age(source='name', direction='younger',
            timestring='%Y.%m.%d', unit='seconds', unit_count=0,
            epoch=1422748800
        )
        self.assertEqual(['snapshot-2015.03.01'], sl.snapshots)
    def test_filter_by_age__name_older_than_past_date(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_age(source='name', direction='older',
            timestring='%Y.%m.%d', unit='seconds', unit_count=0,
            epoch=1456963200
        )
        self.assertEqual(['snapshot-2015.03.01'], sl.snapshots)
    def test_filter_by_age__creation_date_older_than_now(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_age(direction='older', unit='days', unit_count=1)
        self.assertEqual(
            ['snap_name', 'snapshot-2015.03.01'], sorted(sl.snapshots))
    def test_filter_by_age__creation_date_younger_than_now(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_age(direction='younger',
            timestring='%Y.%m.%d', unit='days', unit_count=1
        )
        self.assertEqual([], sl.snapshots)
    def test_filter_by_age__creation_date_younger_than_past_date(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_age(direction='younger',
            timestring='%Y.%m.%d', unit='seconds', unit_count=0,
            epoch=1422748801
        )
        self.assertEqual(['snapshot-2015.03.01'], sl.snapshots)
    def test_filter_by_age__creation_date_older_than_past_date(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        sl = curator.SnapshotList(client, repository=testvars.repo_name)
        sl.filter_by_age(direction='older',
            timestring='%Y.%m.%d', unit='seconds', unit_count=0,
            epoch=1425168001
        )
        self.assertEqual(['snap_name'], sl.snapshots)

class TestIterateFiltersSnaps(TestCase):
    def test_no_filters(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        slo = curator.SnapshotList(client, repository=testvars.repo_name)
        slo.iterate_filters({})
        self.assertEqual(
            ['snap_name', 'snapshot-2015.03.01'], sorted(slo.snapshots)
        )
    def test_no_filtertype(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        slo = curator.SnapshotList(client, repository=testvars.repo_name)
        config = {'filters': [{'no_filtertype':'fail'}]}
        self.assertRaises(
            curator.ConfigurationError, slo.iterate_filters, config)
    def test_invalid_filtertype_class(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        slo = curator.SnapshotList(client, repository=testvars.repo_name)
        config = {'filters': [{'filtertype':12345.6789}]}
        self.assertRaises(
            curator.ConfigurationError, slo.iterate_filters, config)
    def test_invalid_filtertype(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        slo = curator.SnapshotList(client, repository=testvars.repo_name)
        config = yaml.load(testvars.invalid_ft)['actions'][1]
        self.assertRaises(
            curator.ConfigurationError,
            slo.iterate_filters, config
        )
    def test_age_filtertype(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        slo = curator.SnapshotList(client, repository=testvars.repo_name)
        config = yaml.load(testvars.snap_age_ft)['actions'][1]
        slo.iterate_filters(config)
        self.assertEqual(
            ['snap_name', 'snapshot-2015.03.01'], sorted(slo.snapshots))
    def test_pattern_filtertype(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        slo = curator.SnapshotList(client, repository=testvars.repo_name)
        config = yaml.load(testvars.snap_pattern_ft)['actions'][1]
        slo.iterate_filters(config)
        self.assertEqual(
            ['snap_name', 'snapshot-2015.03.01'], sorted(slo.snapshots))
    def test_none_filtertype(self):
        client = Mock()
        client.snapshot.get.return_value = testvars.snapshots
        client.snapshot.get_repository.return_value = testvars.test_repo
        slo = curator.SnapshotList(client, repository=testvars.repo_name)
        config = yaml.load(testvars.snap_none_ft)['actions'][1]
        slo.iterate_filters(config)
        self.assertEqual(
            ['snap_name', 'snapshot-2015.03.01'], sorted(slo.snapshots))
