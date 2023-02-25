import unittest
from firetracker import FireTracker

class TestFireTracker(FireTracker):
    def __init__(self, trail, test_fires):
        self.test_fires = test_fires
        super(TestFireTracker, self).__init__(trail)

    def call_fire_api(self):
        return self.test_fires

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

    def test_add_fire(self):
        tracker = TestFireTracker('CT', self.test_fires)
        try:
            self.assertTrue(any(fire['attributes']['name'] == '🔥🔥🔥 NOT CROSSING TRAIL 🔥🔥🔥' for fire in tracker.state_fires))
            print('test_add_fire passed: test fire was added to state fires.')
        except AssertionError:
            print('Test failed: test fire was not added to state fires.')
    
    def test_fire_not_crossing_trail(self):
        tracker = TestFireTracker('CT', self.test_fires)
        try:
            self.assertTrue(len(tracker.state_fires) - len(tracker.fires_crossing_trail) == 1)
            print('test_fire_not_crossing_trail passed: test fire was not crossing trail.')
        except AssertionError:
            print('test_fire_not_crossing_trail failed: test fire was crossing the trail.')
            print(list(tracker.fires_crossing_trail[0]['shape'].exterior.coords))

    def test_fire_crossing_trail(self):
        tracker = TestFireTracker('CT', self.test_fires)
        try:
            self.assertTrue(len(tracker.fires_crossing_trail) == 1)
            print('test_fire_crossing_trail passed: test fire was crossing trail.')
        except AssertionError:
            print('test_fire_crossing_trail failed: test fire was not crossing the trail.')
    
    def test_sms(self):
        tracker = TestFireTracker('CT', self.test_fires)
        tracker.create_SMS()
        try:
            self.assertTrue(len(tracker.fires_crossing_trail) == 1)
            print('test_fire_crossing_trail passed: test fire was crossing trail.')
        except AssertionError:
            print('test_fire_crossing_trail failed: test fire was not crossing the trail.')

if __name__ == '__main__':
    test_case = FireUnitTesting()
    unittest.main()