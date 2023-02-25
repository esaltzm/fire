import unittest
import copy
from firetracker import FireTracker

class TestFireTracker(FireTracker):
    def __init__(self, trail, test_fires):
        self.test_fires = test_fires
        super(TestFireTracker, self).__init__(trail)
    def call_fire_api(self):
        return copy.deepcopy(self.test_fires)

class FireUnitTesting(unittest.TestCase):

    test_fires = [
        {
            'attributes': {
                'poly_GISAcres': 50,
                'irwin_IncidentName': '🔥🔥🔥 NOT CROSSING TRAIL 🔥🔥🔥',
                'irwin_PercentContained': 95,
            },
            'geometry': {
                'rings': [
                    [[ -107.460916, 38.070289], [ -107.556031, 38.070289], [ -107.556031, 38.135239], [ -107.460916, 38.135239]]
                ]
            }
        },
        {
            'attributes': {
                'poly_GISAcres': 50,
                'irwin_IncidentName': '🔥🔥🔥 IS CROSSING TRAIL 🔥🔥🔥',
                'irwin_PercentContained': 95,
            },
            'geometry': {
                'rings': [
                    [[ -106.330612, 39.673335], [ -106.338165, 39.485990], [ -106.051834, 39.466909], [ -106.066940, 39.689188]]
                ]
            }
        }
    ]

    def test_add_fires(self):
        tracker = TestFireTracker('CT', self.test_fires)
        try:
            self.assertTrue(len(tracker.state_fires) == 2)
            print('test_add_fires PASSED: test fires were added to state fires.')
        except AssertionError:
            print('test_add_fires FAILED: test fires was were added to state fires.')
    
    def test_fire_not_crossing_trail(self):
        tracker = TestFireTracker('CT', self.test_fires)
        try:
            self.assertTrue(any(fire['attributes']['name'] == '🔥🔥🔥 NOT CROSSING TRAIL 🔥🔥🔥' and fire not in tracker.fires_crossing_trail for fire in tracker.state_fires))
            print('test_fire_not_crossing_trail PASSED: test fire was not crossing trail.')
        except AssertionError:
            print('test_fire_not_crossing_trail FAILED: test fire was crossing the trail.')

    def test_fire_crossing_trail(self):
        tracker = TestFireTracker('CT', self.test_fires)
        try:
            self.assertTrue(any(fire['attributes']['name'] == '🔥🔥🔥 IS CROSSING TRAIL 🔥🔥🔥' for fire in tracker.fires_crossing_trail))
            print('test_fire_crossing_trail PASSED: test fire was crossing trail.')
        except AssertionError:
            print('test_fire_crossing_trail FAILED: test fire was not crossing the trail.')
    
    def test_sms(self):
        tracker = TestFireTracker('CT', self.test_fires)
        tracker.create_SMS()
        try:
            self.assertTrue('crosses the CT at mi. 103 to mi. 121' in tracker.text)
            print(f'test_sms PASSED: sms created\n\n{tracker.text}')
        except AssertionError:
            print('test_sms FAILED: sms not created')

if __name__ == '__main__':
    test_case = FireUnitTesting()
    unittest.main()