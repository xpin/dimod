# Copyright 2018 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
# ================================================================================================
import unittest
import fractions
import json
import pickle

try:
    import collections.abc as abc
except ImportError:
    import collections as abc

from collections import OrderedDict

import numpy as np

import dimod


try:
    import pandas as pd
    _pandas = True
except ImportError:
    _pandas = False


class Test_as_samples(unittest.TestCase):
    # tests for as_samples function

    def test_copy_false(self):
        samples_like = np.ones((5, 5))
        labels = list('abcde')
        arr, lab = dimod.as_samples((samples_like, labels))
        np.testing.assert_array_equal(arr, np.ones((5, 5)))
        self.assertEqual(lab, list('abcde'))
        self.assertIs(labels, lab)
        self.assertTrue(np.shares_memory(arr, samples_like))

    def test_dict_with_inconsistent_labels(self):
        with self.assertRaises(ValueError):
            dimod.as_samples(({'a': -1}, 'b'))

    def test_dict_with_labels(self):
        arr, labels = dimod.as_samples(({'a': -1}, 'a'))
        np.testing.assert_array_equal(arr, [[-1]])
        self.assertEqual(labels, ['a'])

    def test_empty_dict(self):
        # one sample, no labels
        arr, labels = dimod.as_samples({})
        np.testing.assert_array_equal(arr, np.zeros((1, 0)))
        self.assertEqual(labels, [])

    def test_empty_list(self):
        # no samples, no labels
        arr, labels = dimod.as_samples([])
        np.testing.assert_array_equal(arr, np.zeros((0, 0)))
        self.assertEqual(labels, [])

    def test_empty_list_labelled(self):
        # no samples, no labels
        arr, labels = dimod.as_samples(([], []))
        np.testing.assert_array_equal(arr, np.zeros((0, 0)))
        self.assertEqual(labels, [])

        # no samples, 1 label
        arr, labels = dimod.as_samples(([], ['a']))
        np.testing.assert_array_equal(arr, np.zeros((0, 1)))
        self.assertEqual(labels, ['a'])

        # no samples, 2 labels
        arr, labels = dimod.as_samples(([], ['a', 'b']))
        np.testing.assert_array_equal(arr, np.zeros((0, 2)))
        self.assertEqual(labels, ['a', 'b'])

    def test_empty_ndarray(self):
        arr, labels = dimod.as_samples(np.ones(0))
        np.testing.assert_array_equal(arr, np.zeros((0, 0)))
        self.assertEqual(labels, [])

    def test_iterator(self):
        with self.assertRaises(TypeError):
            dimod.as_samples(([-1] for _ in range(10)))

    def test_iterator_labelled(self):
        with self.assertRaises(TypeError):
            dimod.as_samples(([-1] for _ in range(10)), 'a')

    def test_list_of_empty(self):
        arr, labels = dimod.as_samples([[], [], []])
        np.testing.assert_array_equal(arr, np.empty((3, 0)))
        self.assertEqual(labels, [])

        arr, labels = dimod.as_samples([{}, {}, {}])
        np.testing.assert_array_equal(arr, np.empty((3, 0)))
        self.assertEqual(labels, [])

        arr, labels = dimod.as_samples(np.empty((3, 0)))
        np.testing.assert_array_equal(arr, np.empty((3, 0)))
        self.assertEqual(labels, [])

    def test_mixed_sampletype(self):
        s1 = [0, 1]
        s2 = OrderedDict([(1, 0), (0, 1)])
        s3 = OrderedDict([(0, 1), (1, 0)])

        arr, labels = dimod.as_samples([s1, s2, s3])
        np.testing.assert_array_equal(arr, [[0, 1], [1, 0], [1, 0]])
        self.assertEqual(labels, [0, 1])

    def test_ndarray(self):
        arr, labels = dimod.as_samples(np.ones(5, dtype=np.int32))
        np.testing.assert_array_equal(arr, np.ones((1, 5)))
        self.assertEqual(labels, list(range(5)))
        self.assertEqual(arr.dtype, np.int32)

    def test_ndarray_labelled(self):
        arr, labels = dimod.as_samples((np.ones(5, dtype=np.int32), 'abcde'))
        np.testing.assert_array_equal(arr, np.ones((1, 5)))
        self.assertEqual(labels, ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(arr.dtype, np.int32)


class TestConstruction(unittest.TestCase):
    def test_from_samples(self):

        nv = 5
        sample_sets = [dimod.SampleSet.from_samples(np.ones((nv, nv), dtype='int8'), dimod.SPIN, energy=np.ones(nv)),
                       dimod.SampleSet.from_samples([[1]*nv for _ in range(nv)], dimod.SPIN, energy=np.ones(nv)),
                       dimod.SampleSet.from_samples([{v: 1 for v in range(nv)} for _ in range(nv)], dimod.SPIN,
                                                    energy=np.ones(nv)),
                       dimod.SampleSet.from_samples((np.ones((nv, nv), dtype='int8'), list(range(nv))), dimod.SPIN,
                                                    energy=np.ones(nv)),
                       ]

        # all should be the same
        self.assertEqual(sample_sets[1:], sample_sets[:-1])

    def test_from_samples_str_labels(self):
        nv = 5
        alpha = 'abcde'
        sample_sets = [dimod.SampleSet.from_samples([{v: 1 for v in alpha} for _ in range(nv)], dimod.SPIN,
                                                    energy=np.ones(nv)),
                       dimod.SampleSet.from_samples((np.ones((nv, nv), dtype='int8'), alpha), dimod.SPIN,
                                                    energy=np.ones(nv)),
                       ]

        # all should be the same
        self.assertEqual(sample_sets[1:], sample_sets[:-1])

    def test_from_samples_single_sample(self):
        ss0 = dimod.SampleSet.from_samples(([-1, +1], 'ab'), dimod.SPIN, energy=1.0)
        ss1 = dimod.SampleSet.from_samples({'a': -1, 'b': +1}, dimod.SPIN, energy=1.0)

        self.assertEqual(ss0, ss1)

        ss2 = dimod.SampleSet.from_samples([-1, +1], dimod.SPIN, energy=1.0)
        ss3 = dimod.SampleSet.from_samples({0: -1, 1: +1}, dimod.SPIN, energy=1.0)

        self.assertEqual(ss2, ss3)

    def test_from_samples_iterator(self):
        ss0 = dimod.SampleSet.from_samples(np.ones((100, 5), dtype='int8'), dimod.BINARY, energy=np.ones(100))

        # ss0.samples() is an iterator, so let's just use that
        with self.assertRaises(TypeError):
            dimod.SampleSet.from_samples(iter(ss0.samples()), dimod.BINARY, energy=ss0.record.energy)

        # should work for iterable
        ss1 = dimod.SampleSet.from_samples(list(ss0.samples()), dimod.BINARY, energy=ss0.record.energy)

        self.assertEqual(len(ss0), len(ss1))
        self.assertEqual(ss0, ss1)

    def test_from_samples_fields_single(self):
        ss = dimod.SampleSet.from_samples({'a': 1, 'b': -1}, dimod.SPIN, energy=1.0, a=5, b='b')

        self.assertIn('a', ss.record.dtype.fields)
        self.assertIn('b', ss.record.dtype.fields)
        self.assertTrue(all(ss.record.a == [5]))
        self.assertTrue(all(ss.record.b == ['b']))

    def test_from_samples_fields_multiple(self):
        ss = dimod.SampleSet.from_samples(np.ones((2, 5)), dimod.BINARY, energy=[0, 0], a=[-5, 5], b=['a', 'b'])

        self.assertIn('a', ss.record.dtype.fields)
        self.assertIn('b', ss.record.dtype.fields)
        self.assertTrue(all(ss.record.a == [-5, 5]))
        self.assertTrue(all(ss.record.b == ['a', 'b']))

    def test_mismatched_shapes(self):
        with self.assertRaises(ValueError):
            dimod.SampleSet.from_samples(np.ones((3, 5)), dimod.SPIN, energy=[5, 5])

    def test_shorter_samples(self):
        ss = dimod.SampleSet.from_samples(np.ones((100, 5), dtype='int8'), dimod.BINARY, energy=np.ones(100))

        self.assertEqual(len(list(ss.samples(n=1))), 1)

    def test_from_samples_empty(self):

        self.assertEqual(len(dimod.SampleSet.from_samples([], dimod.SPIN, energy=[], a=1)), 0)

        self.assertEqual(len(dimod.SampleSet.from_samples(np.empty((0, 0)), dimod.SPIN, energy=[], a=1)), 0)

    def test_from_samples_with_aggregation(self):
        samples = dimod.SampleSet.from_samples(([[-1, 1], [-1, 1]], 'ab'), dimod.SPIN, energy=[0.0, 0.0],
                                               aggregate_samples=True)
        self.assertEqual(samples.aggregate(),
                         dimod.SampleSet.from_samples(([-1, 1], 'ab'), dimod.SPIN, energy=0.0, num_occurrences=2))

    def test_from_bqm_single_sample(self):
        bqm = dimod.BinaryQuadraticModel.from_ising({}, {'ab': -1})
        samples = dimod.SampleSet.from_samples_bqm({'a': -1, 'b': 1}, bqm)
        self.assertEqual(samples,
                         dimod.SampleSet.from_samples(([-1, 1], 'ab'), dimod.SPIN, energy=1))

    def test_from_bqm_with_sorting(self):
        bqm = dimod.BinaryQuadraticModel.from_ising({}, {(0, 1): -1, (1, 2): -1})

        raw = np.triu(np.ones((3, 3)))
        variables = [2, 1, 0]

        samples = dimod.SampleSet.from_samples_bqm((raw, variables), bqm)
        self.assertEqual(samples.variables, [0, 1, 2])
        np.testing.assert_array_equal(np.flip(raw, 1), samples.record.sample)


class TestEq(unittest.TestCase):
    def test_ordered(self):
        # samplesets should be equal regardless of variable order
        ss0 = dimod.SampleSet.from_samples(([-1, 1], 'ab'), dimod.SPIN, energy=0.0)
        ss1 = dimod.SampleSet.from_samples(([1, -1], 'ba'), dimod.SPIN, energy=0.0)
        ss2 = dimod.SampleSet.from_samples(([1, -1], 'ab'), dimod.SPIN, energy=0.0)
        ss3 = dimod.SampleSet.from_samples(([1, -1], 'ac'), dimod.SPIN, energy=0.0)

        self.assertEqual(ss0, ss1)
        self.assertNotEqual(ss0, ss2)
        self.assertNotEqual(ss1, ss3)


class TestAggregate(unittest.TestCase):
    def test_aggregate_simple(self):
        samples = dimod.SampleSet.from_samples(([[-1, 1], [-1, 1]], 'ab'), dimod.SPIN, energy=[0.0, 0.0])

        self.assertEqual(samples.aggregate(),
                         dimod.SampleSet.from_samples(([-1, 1], 'ab'), dimod.SPIN, energy=0.0, num_occurrences=2))

        # original should not be changed
        self.assertEqual(samples,
                         dimod.SampleSet.from_samples(([[-1, 1], [-1, 1]], 'ab'), dimod.SPIN, energy=[0.0, 0.0]))

    def test_order_preservation_2x2_unique(self):
        bqm = dimod.BinaryQuadraticModel({}, {'ab': 1}, 0, dimod.SPIN)

        # these are unique so order should be preserved
        ss1 = dimod.SampleSet.from_samples_bqm([{'a': 1, 'b': -1},
                                                {'a': -1, 'b': 1}],
                                               bqm)
        ss2 = ss1.aggregate()

        self.assertEqual(ss1, ss2)

    def test_order_preservation(self):
        bqm = dimod.BinaryQuadraticModel({}, {'ab': 1}, 0, dimod.SPIN)

        ss1 = dimod.SampleSet.from_samples_bqm([{'a': 1, 'b': -1},
                                                {'a': -1, 'b': 1},
                                                {'a': 1, 'b': -1}],
                                               bqm)
        ss2 = ss1.aggregate()

        target = dimod.SampleSet.from_samples_bqm([{'a': 1, 'b': -1},
                                                   {'a': -1, 'b': 1}],
                                                  bqm,
                                                  num_occurrences=[2, 1])

        self.assertEqual(target, ss2)

    def test_order_preservation_doubled(self):
        bqm = dimod.BinaryQuadraticModel({}, {'ab': 1, 'bc': -1}, 0, dimod.SPIN)
        ss1 = dimod.SampleSet.from_samples_bqm(([[1, 1, 0],
                                                 [1, 0, 0],
                                                 [0, 0, 0],
                                                 [0, 0, 0],
                                                 [1, 1, 0],
                                                 [1, 0, 0],
                                                 [0, 0, 0]], 'abc'),
                                               bqm)

        target = dimod.SampleSet.from_samples_bqm(([[1, 1, 0],
                                                    [1, 0, 0],
                                                    [0, 0, 0]], 'abc'),
                                                  bqm,
                                                  num_occurrences=[2, 2, 3])

        self.assertEqual(target, ss1.aggregate())

    def test_num_occurences(self):
        samples = [[-1, -1, +1],
                   [-1, +1, +1],
                   [-1, +1, +1],
                   [-1, -1, -1],
                   [-1, +1, +1]]
        agg_samples = [[-1, -1, +1],
                       [-1, +1, +1],
                       [-1, -1, -1]]
        labels = 'abc'

        sampleset = dimod.SampleSet.from_samples((samples, labels), energy=0,
                                                 vartype=dimod.SPIN)
        aggregated = dimod.SampleSet.from_samples((agg_samples, labels), energy=0,
                                                  vartype=dimod.SPIN,
                                                  num_occurrences=[1, 3, 1])

        self.assertEqual(sampleset.aggregate(), aggregated)


class TestAppend(unittest.TestCase):
    def test_sampleset1_append1(self):
        sampleset = dimod.SampleSet.from_samples({'a': -1, 'b': 1}, dimod.SPIN, energy=0)
        new = sampleset.append_variables({'c': -1, 'd': -1})

        target = dimod.SampleSet.from_samples({'a': -1, 'b': 1, 'c': -1, 'd': -1}, dimod.SPIN, energy=0)

        self.assertEqual(new, target)

    def test_sampleset2_append1(self):
        sampleset = dimod.SampleSet.from_samples([{'a': -1, 'b': 1}, {'a': -1, 'b': -1}],
                                                 dimod.SPIN, energy=0)
        new = sampleset.append_variables({'c': -1, 'd': -1})

        target = dimod.SampleSet.from_samples([{'a': -1, 'b': 1, 'c': -1, 'd': -1},
                                               {'a': -1, 'b': -1, 'c': -1, 'd': -1}],
                                              dimod.SPIN, energy=0)

        self.assertEqual(new, target)

    def test_sampleset2_append2(self):
        sampleset = dimod.SampleSet.from_samples([{'a': -1, 'b': 1}, {'a': -1, 'b': -1}],
                                                 dimod.SPIN, energy=0)
        new = sampleset.append_variables([{'c': -1, 'd': -1}, {'c': 1, 'd': 1}])

        target = dimod.SampleSet.from_samples([{'a': -1, 'b': 1, 'c': -1, 'd': -1},
                                               {'a': -1, 'b': -1, 'c': 1, 'd': 1}],
                                              dimod.SPIN, energy=0)

        self.assertEqual(new, target)

    def test_sampleset2_append3(self):
        sampleset = dimod.SampleSet.from_samples([{'a': -1, 'b': 1}, {'a': -1, 'b': -1}],
                                                 dimod.SPIN, energy=0)

        with self.assertRaises(ValueError):
            sampleset.append_variables([{'c': -1, 'd': -1}, {'c': 1, 'd': 1}, {'c': -1, 'd': -1}])

    def test_overlapping_variables(self):
        sampleset = dimod.SampleSet.from_samples([{'a': -1, 'b': 1}, {'a': -1, 'b': -1}],
                                                 dimod.SPIN, energy=0)

        with self.assertRaises(ValueError):
            sampleset.append_variables([{'c': -1, 'd': -1, 'a': -1}])

    def test_two_samplesets(self):
        sampleset0 = dimod.SampleSet.from_samples([{'a': -1, 'b': 1}, {'a': -1, 'b': -1}],
                                                  dimod.SPIN, energy=[-2, 2])
        sampleset1 = dimod.SampleSet.from_samples([{'c': -1, 'd': 1}, {'c': -1, 'd': -1}],
                                                  dimod.SPIN, energy=[-1, 1])

        target = dimod.SampleSet.from_samples([{'a': -1, 'b': 1, 'c': -1, 'd': 1},
                                               {'a': -1, 'b': -1, 'c': -1, 'd': -1}],
                                              dimod.SPIN, energy=[-2, 2])

        self.assertEqual(sampleset0.append_variables(sampleset1), target)


class TestLowest(unittest.TestCase):
    def test_all_equal(self):
        sampleset = dimod.ExactSolver().sample_ising({}, {'ab': 0})
        self.assertEqual(sampleset, sampleset.lowest())

    def test_empty(self):
        sampleset = dimod.SampleSet.from_samples(([], 'ab'), energy=[], vartype=dimod.SPIN)
        self.assertEqual(sampleset, sampleset.lowest())

    def test_tolerance(self):
        sampleset = dimod.ExactSolver().sample_ising({'a': .001}, {('a', 'b'): -1})

        self.assertEqual(sampleset.lowest(atol=.1), sampleset.truncate(2))
        self.assertEqual(sampleset.lowest(atol=0), sampleset.truncate(1))


class TestPickle(unittest.TestCase):
    def test_without_future(self):
        sampleset = dimod.SampleSet.from_samples([{'a': -1, 'b': 1},
                                                  {'a': -1, 'b': -1}],
                                                 dimod.SPIN, energy=0)
        sampleset.info.update({'a': 5})

        new = pickle.loads(pickle.dumps(sampleset))

        self.assertEqual(new, sampleset)
        self.assertEqual(new.info, {'a': 5})


class TestTruncate(unittest.TestCase):
    def test_typical(self):
        bqm = dimod.BinaryQuadraticModel.from_ising({v: -1 for v in range(100)}, {})
        samples = dimod.SampleSet.from_samples_bqm(np.tril(np.ones(100)), bqm.binary)

        # by default should be in reverse order
        new = samples.truncate(10)
        self.assertEqual(len(new), 10)
        for n, sample in enumerate(new.samples()):
            for v, val in sample.items():
                if v > 100 - n - 1:
                    self.assertEqual(val, 0)
                else:
                    self.assertEqual(val, 1)

    def test_unordered(self):
        bqm = dimod.BinaryQuadraticModel.from_ising({v: -1 for v in range(100)}, {})
        samples = dimod.SampleSet.from_samples_bqm(np.triu(np.ones(100)), bqm.binary)

        # now undordered
        new = samples.truncate(10, sorted_by=None)
        self.assertEqual(len(new), 10)
        for n, sample in enumerate(new.samples()):
            for v, val in sample.items():
                if v < n:
                    self.assertEqual(val, 0)
                else:
                    self.assertEqual(val, 1)


class TestSlice(unittest.TestCase):
    def test_typical(self):
        bqm = dimod.BinaryQuadraticModel.from_ising({v: -1 for v in range(100)}, {})
        sampleset = dimod.SampleSet.from_samples_bqm(np.tril(np.ones(100)), bqm.binary)

        # `:10` is equal to `truncate(10)`
        self.assertEqual(sampleset.slice(10), sampleset.truncate(10))

    def test_unordered(self):
        bqm = dimod.BinaryQuadraticModel.from_ising({v: -1 for v in range(100)}, {})
        sampleset = dimod.SampleSet.from_samples_bqm(np.triu(np.ones(100)), bqm.binary)

        # `:10` but for the unordered case
        self.assertEqual(sampleset.slice(10, sorted_by=None), sampleset.truncate(10, sorted_by=None))

    def test_null_slice(self):
        energies = list(range(10))
        sampleset = dimod.SampleSet.from_samples(np.ones((10, 1)), dimod.SPIN, energy=energies)

        self.assertTrue((sampleset.slice().record.energy == energies).all())

    def test_slice_stop_only(self):
        energies = list(range(10))
        sampleset = dimod.SampleSet.from_samples(np.ones((10, 1)), dimod.SPIN, energy=energies)

        self.assertTrue((sampleset.slice(3).record.energy == energies[:3]).all())
        self.assertTrue((sampleset.slice(-3).record.energy == energies[:-3]).all())

    def test_slice_range(self):
        energies = list(range(10))
        sampleset = dimod.SampleSet.from_samples(np.ones((10, 1)), dimod.SPIN, energy=energies)

        self.assertTrue((sampleset.slice(3, 5).record.energy == energies[3:5]).all())
        self.assertTrue((sampleset.slice(3, -3).record.energy == energies[3:-3]).all())
        self.assertTrue((sampleset.slice(-3, None).record.energy == energies[-3:]).all())

    def test_slice_stride(self):
        energies = list(range(10))
        sampleset = dimod.SampleSet.from_samples(np.ones((10, 1)), dimod.SPIN, energy=energies)

        self.assertTrue((sampleset.slice(3, -3, 2).record.energy == energies[3:-3:2]).all())
        self.assertTrue((sampleset.slice(None, None, 2).record.energy == energies[::2]).all())
        self.assertTrue((sampleset.slice(None, None, -1).record.energy == energies[::-1]).all())

    def test_custom_ordering(self):
        custom = list(range(10))
        sampleset = dimod.SampleSet.from_samples(np.ones((10, 1)), dimod.SPIN, energy=None, custom=custom)

        self.assertTrue((sampleset.slice(3, sorted_by='custom').record.custom == custom[:3]).all())
        self.assertTrue((sampleset.slice(3, -3, sorted_by='custom').record.custom == custom[3:-3]).all())
        self.assertTrue((sampleset.slice(None, None, -1, sorted_by='custom').record.custom == custom[::-1]).all())

    def test_kwargs(self):
        sampleset = dimod.SampleSet.from_samples(np.ones((10, 1)), dimod.SPIN, energy=None)

        with self.assertRaises(TypeError):
            sampleset.slice(1, sortedby='invalid-kwarg')


class TestIteration(unittest.TestCase):
    def test_data_reverse(self):
        bqm = dimod.BinaryQuadraticModel.from_ising({}, {'ab': -1})
        sampleset = dimod.SampleSet.from_samples_bqm([{'a': -1, 'b': 1}, {'a': 1, 'b': 1}], bqm)

        samples = list(sampleset.data())
        reversed_samples = list(sampleset.data(reverse=True))
        self.assertEqual(samples, list(reversed(reversed_samples)))

    def test_iterator(self):
        # deprecated feature
        bqm = dimod.BinaryQuadraticModel.from_ising({}, {'ab': -1})
        sampleset = dimod.SampleSet.from_samples_bqm([{'a': -1, 'b': 1}, {'a': 1, 'b': 1}], bqm)
        self.assertIsInstance(sampleset.samples(), abc.Iterator)
        self.assertIsInstance(sampleset.samples(n=2), abc.Iterator)
        spl = next(sampleset.samples())
        self.assertEqual(spl, {'a': 1, 'b': 1})


class TestSerialization(unittest.TestCase):
    def test_empty_with_bytes(self):
        sampleset = dimod.SampleSet.from_samples([], dimod.BINARY, energy=[])

        dct = sampleset.to_serializable(use_bytes=True)

        new = dimod.SampleSet.from_serializable(dct)

        self.assertEqual(sampleset, new)

    def test_triu_with_bytes(self):
        num_variables = 100
        num_samples = 100
        samples = 2*np.triu(np.ones((num_samples, num_variables)), -4) - 1
        bqm = dimod.BinaryQuadraticModel.from_ising({v: .1*v for v in range(num_variables)}, {})
        sampleset = dimod.SampleSet.from_samples_bqm(samples, bqm)

        dct = sampleset.to_serializable(use_bytes=True)

        new = dimod.SampleSet.from_serializable(dct)

        self.assertEqual(sampleset, new)

    def test_functional_simple_shapes(self):
        for ns in range(1, 9):
            for nv in range(1, 15):

                raw = np.random.randint(2, size=(ns, nv))

                if ns % 2:
                    vartype = dimod.SPIN
                    raw = 2 * raw - 1
                else:
                    vartype = dimod.BINARY

                samples = dimod.SampleSet.from_samples(raw, vartype, energy=np.ones(ns))
                new_samples = dimod.SampleSet.from_serializable(samples.to_serializable())
                self.assertEqual(samples, new_samples)

    def test_functional_with_info(self):
        sampleset = dimod.SampleSet.from_samples([[-1, 1], [1, -1]], energy=-1,
                                                 vartype=dimod.SPIN,
                                                 info={'hello': 'world'})

        new = dimod.SampleSet.from_serializable(sampleset.to_serializable())

        self.assertEqual(new.info, sampleset.info)

    def test_functional_json(self):
        nv = 4
        ns = 7

        raw = np.random.randint(2, size=(ns, nv))

        samples = dimod.SampleSet.from_samples(raw, dimod.BINARY, energy=np.ones(ns))

        s = json.dumps(samples.to_serializable())
        new_samples = dimod.SampleSet.from_serializable(json.loads(s))
        self.assertEqual(samples, new_samples)

    def test_functional_str(self):
        nv = 4
        ns = 7

        raw = np.random.randint(2, size=(ns, nv))

        samples = dimod.SampleSet.from_samples((raw, 'abcd'), dimod.BINARY, energy=np.ones(ns))

        s = json.dumps(samples.to_serializable())
        new_samples = dimod.SampleSet.from_serializable(json.loads(s))
        self.assertEqual(samples, new_samples)

    def test_from_serializable_empty_v1(self):
        samples = dimod.SampleSet.from_samples([], dimod.BINARY, energy=[])

        s = """
        {"record": {"sample": {"data": "", "shape": [0, 0], "dtype": "int8"},
                    "energy": {"data": "", "shape": [0], "dtype": "float64"},
                    "num_occurrences": {"data": "", "shape": [0], "dtype": "int64"}},
         "variable_type": "BINARY", "info": {},
         "version": {"dimod": "0.8.5", "sampleset_schema": "1.0.0"},
         "variable_labels": []}"""

        self.assertEqual(samples, dimod.SampleSet.from_serializable(json.loads(s)))

    def test_from_serializable_empty_variables_v1(self):
        samples = dimod.SampleSet.from_samples(([], 'abcd'), dimod.BINARY, energy=[])

        s = """
        {"record": {"sample": {"data": "", "shape": [0, 4], "dtype": "int8"},
                    "energy": {"data": "", "shape": [0], "dtype": "float64"},
                    "num_occurrences": {"data": "", "shape": [0], "dtype": "int64"}},
         "variable_type": "BINARY", "info": {},
         "version": {"dimod": "0.8.5", "sampleset_schema": "1.0.0"},
         "variable_labels": ["a", "b", "c", "d"]}"""

        self.assertEqual(samples, dimod.SampleSet.from_serializable(json.loads(s)))

    def test_from_serializable_triu_v1(self):
        samples = dimod.SampleSet.from_samples(np.triu(np.ones((10, 10))),
                                               dimod.BINARY,
                                               energy=np.arange(-1, 1, 10))

        s = """
        {"record": {"sample": {"data": "/9/z/H8PwfA8BwDAEA==",
                               "shape": [10, 10], "dtype": "float64"},
                    "energy": {"data": "//////////////////////////////////////////////////////////////////////////////////////////////////////////8=",
                               "shape": [10], "dtype": "int64"},
                    "num_occurrences": {"data": "AQAAAAAAAAABAAAAAAAAAAEAAAAAAAAAAQAAAAAAAAABAAAAAAAAAAEAAAAAAAAAAQAAAAAAAAABAAAAAAAAAAEAAAAAAAAAAQAAAAAAAAA=",
                               "shape": [10], "dtype": "int64"}},
         "variable_type": "BINARY", "info": {},
         "version": {"dimod": "0.8.5", "sampleset_schema": "1.0.0"},
         "variable_labels": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}"""

        self.assertEqual(samples, dimod.SampleSet.from_serializable(json.loads(s)))

    def test_tuple_variable_labels(self):
        sampleset = dimod.SampleSet.from_samples(([], [(0, 0), (0, 1), ("a", "b", 2)]), dimod.BINARY, energy=[])

        json_str = json.dumps(sampleset.to_serializable())

        new = dimod.SampleSet.from_serializable(json.loads(json_str))

        self.assertEqual(sampleset, new)

    def test_numpy_variable_labels(self):
        h = {0: 0, 1: 1, np.int64(2): 2, np.float(3): 3,
             fractions.Fraction(4, 1): 4, fractions.Fraction(5, 2): 5,
             '6': 6}

        sampleset = dimod.NullSampler().sample_ising(h, {})

        json.dumps(sampleset.to_serializable())


@unittest.skipUnless(_pandas, "no pandas present")
class TestPandas(unittest.TestCase):
    def test_simple(self):
        samples = dimod.SampleSet.from_samples(([[-1, 1, -1], [-1, -1, 1]], 'abc'),
                                               dimod.SPIN, energy=[-.5, .5])
        df = samples.to_pandas_dataframe()

        other = pd.DataFrame([[-1, 1, -1, -.5, 1], [-1, -1, 1, .5, 1]],
                             columns=['a', 'b', 'c', 'energy', 'num_occurrences'])

        pd.testing.assert_frame_equal(df, other, check_dtype=False)

    def test_sample_column(self):
        samples = dimod.SampleSet.from_samples(([[-1, 1, -1], [-1, -1, 1]], 'abc'),
                                               dimod.SPIN, energy=[-.5, .5])
        df = samples.to_pandas_dataframe(sample_column=True)

        other = pd.DataFrame([[{'a': -1, 'b': 1, 'c': -1}, -0.5, 1],
                              [{'a': -1, 'b': -1, 'c': 1}, 0.5, 1]],
                             columns=['sample', 'energy', 'num_occurrences'])

        pd.testing.assert_frame_equal(df, other, check_dtype=False)


class TestFirst(unittest.TestCase):
    # SampleSet.first property
    def test_empty(self):
        with self.assertRaises(ValueError):
            dimod.SampleSet.from_samples([], dimod.SPIN, energy=[]).first


class TestDataVectors(unittest.TestCase):
    # SampleSet.data_vectors property
    def test_empty(self):
        ss = dimod.SampleSet.from_samples([], dimod.SPIN, energy=[])

        self.assertEqual(set(ss.data_vectors), {'energy', 'num_occurrences'})
        for field, vector in ss.data_vectors.items():
            np.testing.assert_array_equal(vector, [])

    def test_view(self):
        # make sure that the vectors are views
        ss = dimod.SampleSet.from_samples([[-1, 1], [1, 1]], dimod.SPIN, energy=[5, 5])

        self.assertEqual(set(ss.data_vectors), {'energy', 'num_occurrences'})
        for field, vector in ss.data_vectors.items():
            np.shares_memory(vector, ss.record)


class Test_concatenate(unittest.TestCase):
    def test_simple(self):
        ss0 = dimod.SampleSet.from_samples([-1, +1], dimod.SPIN, energy=-1)
        ss1 = dimod.SampleSet.from_samples([+1, -1], dimod.SPIN, energy=-1)
        ss2 = dimod.SampleSet.from_samples([[+1, +1], [-1, -1]], dimod.SPIN, energy=[1, 1])

        comb = dimod.concatenate((ss0, ss1, ss2))

        out = dimod.SampleSet.from_samples([[-1, +1], [+1, -1], [+1, +1], [-1, -1]], dimod.SPIN, energy=[-1, -1, 1, 1])

        self.assertEqual(comb, out)
        np.testing.assert_array_equal(comb.record.sample, out.record.sample)

    def test_variables_order(self):
        ss0 = dimod.SampleSet.from_samples(([-1, +1], 'ab'), dimod.SPIN, energy=-1)
        ss1 = dimod.SampleSet.from_samples(([-1, +1], 'ba'), dimod.SPIN, energy=-1)
        ss2 = dimod.SampleSet.from_samples(([[+1, +1], [-1, -1]], 'ab'), dimod.SPIN, energy=[1, 1])

        comb = dimod.concatenate((ss0, ss1, ss2))

        out = dimod.SampleSet.from_samples(([[-1, +1], [+1, -1], [+1, +1], [-1, -1]], 'ab'),
                                           dimod.SPIN, energy=[-1, -1, 1, 1])

        self.assertEqual(comb, out)
        np.testing.assert_array_equal(comb.record.sample, out.record.sample)

    def test_variables_order(self):
        ss0 = dimod.SampleSet.from_samples(([-1, +1], 'ab'), dimod.SPIN, energy=-1)
        ss1 = dimod.SampleSet.from_samples(([-1, +1], 'ba'), dimod.SPIN, energy=-1)
        ss2 = dimod.SampleSet.from_samples(([[+1, +1], [-1, -1]], 'ab'), dimod.SPIN, energy=[1, 1])

        comb = dimod.concatenate((ss0, ss1, ss2))

        out = dimod.SampleSet.from_samples(([[-1, +1], [+1, -1], [+1, +1], [-1, -1]], 'ab'),
                                           dimod.SPIN, energy=[-1, -1, 1, 1])

        self.assertEqual(comb, out)
        np.testing.assert_array_equal(comb.record.sample, out.record.sample)

    def test_variables_order_and_vartype(self):
        ss0 = dimod.SampleSet.from_samples(([-1, +1], 'ab'), dimod.SPIN, energy=-1)
        ss1 = dimod.SampleSet.from_samples(([-1, +1], 'ba'), dimod.SPIN, energy=-1)
        ss2 = dimod.SampleSet.from_samples(([[1, 1], [0, 0]], 'ab'), dimod.BINARY, energy=[1, 1])

        comb = dimod.concatenate((ss0, ss1, ss2))

        out = dimod.SampleSet.from_samples(([[-1, +1], [+1, -1], [+1, +1], [-1, -1]], 'ab'),
                                           dimod.SPIN, energy=[-1, -1, 1, 1])

        self.assertEqual(comb, out)
        np.testing.assert_array_equal(comb.record.sample, out.record.sample)

    def test_empty(self):
        with self.assertRaises(ValueError):
            dimod.concatenate([])


class TestWriteable(unittest.TestCase):
    def test_locked(self):
        ss = dimod.SampleSet.from_samples(([[1, 1], [0, 0]], 'ab'),
                                          dimod.BINARY, energy=[1, 1])

        ss.is_writeable = False

        with self.assertRaises(dimod.exceptions.WriteableError):
            ss.relabel_variables({'a': 'c'})

        with self.assertRaises(dimod.exceptions.WriteableError):
            ss.change_vartype('SPIN', inplace=True)
