"""Behavioral invariants and regressions for the classical decoder."""
import json
import random
import unittest
from pathlib import Path
from unittest.mock import patch

import fibonacci_decoder as d


class DecoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L, cls.H = 8, 4
        cls.sym = d.create_symmetry(8, 4, [1] + [0]*7)
        cls.weights = d.build_edge_weight_matrix(cls.sym, 8, 4, .08)

    def decode(self, error, mode='distance'):
        snaps = []
        w = self.weights if mode == 'distance' else d.build_edge_weight_matrix(self.sym,8,4,.08,mode)
        outcome, rounds = d.test_code(.08,8,4,0,self.sym,w,preset_error=error,snapshots=snaps)
        vector = [int(i in error) for i in range(32)]
        for snap in snaps:
            residual = [a ^ b for a,b in zip(vector,snap['prediction'])]
            self.assertEqual(d.measure_all_stabilizers(residual,8,4),snap['residual'])
            self.assertEqual(sum(snap['residual']),snap['defects'])
        self.assertEqual(outcome == 1, snaps[-1]['prediction'] == vector)
        self.assertLessEqual(rounds, 33)
        return outcome, snaps

    def test_torus_neighbors_are_inverses(self):
        for v in range(32):
            self.assertEqual(d.west_vertex(d.east_vertex(v,8),8),v)
            self.assertEqual(d.south_vertex(d.north_vertex(v,8,4),8,4),v)

    def test_every_single_flip_has_expected_syndrome_and_even_symmetry_parity(self):
        for q in range(32):
            s = d.measure_all_stabilizers([int(i == q) for i in range(32)],8,4)
            self.assertEqual({i for i,x in enumerate(s) if x},
                             {q,d.south_vertex(q,8,4),d.east_vertex(q,8),d.west_vertex(q,8)})
            for dy in range(4):
                for dx in range(8):
                    translated = [((v//8+dy)%4)*8 + (v%8+dx)%8 for v in self.sym]
                    self.assertEqual(sum(s[v] for v in translated)%2,0)

    def test_zero_error_needs_no_rounds(self):
        outcome, snaps = self.decode([])
        self.assertEqual(outcome,1)
        self.assertEqual(len(snaps),1)

    def test_nonzero_codeword_is_not_exact_recovery(self):
        outcome, snaps = self.decode(list(range(32)))
        self.assertEqual(outcome,0)
        self.assertEqual(snaps[-1]['defects'],0)

    def test_all_single_bit_errors_recover(self):
        for q in range(32):
            self.assertEqual(self.decode([q])[0],1)

    def test_worked_example_and_snapshot_consistency(self):
        for mode in ['distance','degeneracy']:
            self.assertEqual(self.decode([3,7,12,14,16,20,27,29],mode)[0],1)

    def test_seeded_random_cases_and_statistics(self):
        rng=random.Random(42)
        for _ in range(30):
            self.decode([i for i in range(32) if rng.random()<.12])
        a=d.compute_failure_number(.08,8,4,0,20,self.sym,self.weights,rng=random.Random(3))
        b=d.compute_failure_number(.08,8,4,0,20,self.sym,self.weights,rng=random.Random(3))
        self.assertEqual(a,b)
        self.assertEqual(a['success']+a['incorrect']+a['give_up'],20)

    def test_bfs_counts_multiple_shortest_paths(self):
        distance,count=d.shortest_paths_from(0,[{1,2},{0,3},{0,3},{1,2}],4)
        self.assertEqual(distance,[0,1,1,2])
        self.assertEqual(count,[1,1,1,2])

    def test_matching_minimizes_cost_including_negative_weights(self):
        weights=[[0,9,-4,2],[9,0,2,-4],[-4,2,0,9],[2,-4,9,0]]
        with patch.object(d,'_HAVE_NX',False):
            a,b=d.minimum_weight_matching_symmetry_index(list(range(4)),weights)
        self.assertEqual(sum(weights[i][j] for i,j in zip(a,b)),-8)
        if d._HAVE_NX:
            pairs=d._matching_via_networkx(weights)
            self.assertEqual(sum(weights[i][j] for i,j in pairs),-8)

    def test_invalid_inputs_fail_clearly(self):
        for L,H,row in [(7,3,[1]*7),(8,5,[1]*8),(8,4,[1]),(8,4,[2]*8)]:
            with self.assertRaises(ValueError): d.create_symmetry(L,H,row)
        for p,mode in [(0,'distance'),(1,'degeneracy'),(.1,'typo')]:
            with self.assertRaises(ValueError): d.build_edge_weight_matrix(self.sym,8,4,p,mode)
        with self.assertRaises(ValueError): self.decode([-1])
        with self.assertRaises(ValueError): d.minimum_weight_matching_symmetry_index([0],self.weights)
        with self.assertRaises(ValueError): d._matching_via_dp([[0]*22 for _ in range(22)])
        with self.assertRaises(ValueError): d.compute_failure_number(.1,8,4,0,0,self.sym,self.weights)

    def test_notebook_has_no_broken_saved_widget_state(self):
        nb=json.loads((Path(__file__).resolve().parents[1]/'Fibonacci_Decoder.ipynb').read_text(encoding='utf-8'))
        self.assertEqual(nb['nbformat'],4)
        self.assertNotIn('widgets',nb['metadata'])
        ids=[c['id'] for c in nb['cells']]
        self.assertEqual(len(ids),len(set(ids)))
        for c in nb['cells']:
            if c['cell_type']=='code':
                self.assertEqual(c['outputs'],[])
                self.assertIsNone(c['execution_count'])
        # The walkthrough and importable module share the same decoder code.
        code='\n\n'.join(''.join(nb['cells'][i]['source']) for i in [2,4,6,8,12,14,16,18,20])
        module=(Path(d.__file__)).read_text(encoding='utf-8')
        self.assertTrue(module.endswith(code))


if __name__ == '__main__':
    unittest.main()
