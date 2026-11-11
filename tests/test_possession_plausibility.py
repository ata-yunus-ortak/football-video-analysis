"""Synthetic checks of the submission plausibility tool."""
import os, tempfile, unittest
import numpy as np
try:  # needs pandas (requirements-possession.txt)
    from possession.plausibility import stats, check, RANGES
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False


def _labels(seed=0, dead=0.4):
    rng = np.random.default_rng(seed); out = []
    for half in range(2):
        t = 0
        while t < 47 * 60 * 25:
            n = int(rng.integers(40, 300)); out += ['HA'[int(rng.integers(0, 2))]] * n; t += n
            if rng.random() < dead:
                n = int(rng.integers(100, 900)); out += ['D'] * n; t += n
        if half == 0:
            out += ['D'] * (15 * 60 * 25)
    return np.array(['D'] * 5000 + out + ['D'] * 5000)


@unittest.skipUnless(HAVE_DEPS, 'possession dependencies not installed')
class PlausibilityTests(unittest.TestCase):
    def test_reasonable_match_passes_and_break_is_excluded(self):
        s = stats(_labels())
        self.assertTrue(85 < s['play_minutes'] < 115)
        self.assertTrue(all(RANGES[k][0] <= s[k] <= RANGES[k][1] for k in RANGES), s)

    def test_degenerate_outputs_fail(self):
        with tempfile.TemporaryDirectory() as d:
            for name, lab in (('alldead', np.full(199319, 'D')), ('onespell', np.r_[np.full(1000, 'D'), np.full(198319, 'H')])):
                p = os.path.join(d, name + '.csv')
                with open(p, 'w') as f:
                    f.write('frame,label\n' + '\n'.join(f'{i},{v}' for i, v in enumerate(lab)) + '\n')
                self.assertFalse(all(check(p).values()))


if __name__ == '__main__':
    unittest.main()
