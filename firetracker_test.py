import unittest
from firetracker import FireTracker

class TestFireTracker(FireTracker):
    def __init__(self, trail, test_fire):
        super().__init__(trail)
        self.state_fires.append(test_fire)

class FireUnitTesting(unittest.TestCase):
    test_fire = {
        'attributes': {
            'poly_GISAcres': 50,
            'irwin_IncidentName': '🔥🔥🔥 TEST FIRE 🔥🔥🔥',
            'irwin_PercentContained': 95,
        },
        'geometry': {
            'rings': [
                [(38.070289, -107.460916), (38.070289, 107.556031), (38.135239, -107.556031), (38.135239, -107.460916)]
            ]
        }
    }
    def test_add_fire(self):
        tracker = TestFireTracker('CT', self.test_fire)
        try:
            self.assertTrue(any(fire.get('attributes', {}).get('irwin_IncidentName') == '🔥🔥🔥 TEST FIRE 🔥🔥🔥' for fire in tracker.state_fires))
            print('Test passed: test fire was added to current fires.')
        except AssertionError:
            print('Test failed: test fire was not added to current fires.')

if __name__ == '__main__':
    test_case = FireUnitTesting()
    unittest.main()