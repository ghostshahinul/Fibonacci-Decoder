"""Run a fixed error or a reproducible Monte Carlo experiment."""
import argparse
import json
import random

from fibonacci_decoder import build_edge_weight_matrix, compute_failure_number, create_symmetry, test_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, default=8, help='Power of two >= 4; height is size/2')
    parser.add_argument('--p', type=float, default=0.08)
    parser.add_argument('--mode', choices=['distance', 'degeneracy'], default='distance')
    parser.add_argument('--samples', type=int, default=0, help='Positive count enables Monte Carlo')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    if args.samples < 0:
        parser.error('--samples must be nonnegative')
    L, H = args.size, args.size // 2
    try:
        symmetry = create_symmetry(L, H, [1] + [0] * (L - 1))
        weights = build_edge_weight_matrix(symmetry, L, H, args.p, mode=args.mode)
    except ValueError as exc:
        parser.error(str(exc))
    if args.samples:
        result = compute_failure_number(args.p, L, H, 0, args.samples, symmetry, weights,
                                        rng=random.Random(args.seed))
    else:
        error = [3, 7, 12, 14, 16, 20, 27, 29] if L == 8 else [0]
        snapshots = []
        outcome, rounds = test_code(args.p, L, H, 0, symmetry, weights,
                                    preset_error=error, snapshots=snapshots)
        result = {'error': error, 'outcome': {0: 'incorrect', 1: 'exact recovery', 2: 'gave up'}[outcome],
                  'rounds': rounds, 'residual_defects': [s['defects'] for s in snapshots]}
    print(json.dumps({'size': L, 'height': H, 'p': args.p, 'mode': args.mode,
                      'seed': args.seed, 'result': result}, indent=2))


if __name__ == '__main__':
    main()
