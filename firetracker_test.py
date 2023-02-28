import unittest
import copy
from typing import *
from firetracker import FireTracker
import matplotlib.pyplot as plt

class TestFireTracker(FireTracker):

    def __init__(self, trail: str, test_fires: List[object]) -> None:
        self.test_fires = test_fires
        super(TestFireTracker, self).__init__(trail)

    def call_fire_api(self) -> List[object]:
        return copy.deepcopy(self.test_fires)

class FireUnitTesting(unittest.TestCase):

    trail = 'CDT'

    test_fires_template = [
        {
            'attributes': {
                'poly_GISAcres': 50,
                'irwin_IncidentName': '🔥🔥🔥 NOT CROSSING TRAIL 🔥🔥🔥',
                'irwin_PercentContained': 95,
            },
            'geometry': {
                'rings': []
            }
        },
        {
            'attributes': {
                'poly_GISAcres': 50,
                'irwin_IncidentName': '🔥🔥🔥 IS CROSSING TRAIL 🔥🔥🔥',
                'irwin_PercentContained': 95,
            },
            'geometry': {
                'rings': []
            }
        }
    ]

    test_fires = {
        'CT': [
            [[ -107.460916, 38.070289], [ -107.556031, 38.070289], [ -107.556031, 38.135239], [ -107.460916, 38.135239]],
            [[ -106.330612, 39.673335], [ -106.338165, 39.485990], [ -106.051834, 39.466909], [ -106.066940, 39.689188]]
        ],
        'PNT': [
            [[-120.264561, 48.098639], [-120.264561, 47.348513], [-118.880284, 47.329900], [-118.902256, 48.039908]],
            [[-114.477539, 49.038410], [-114.435321, 48.271664], [-113.113007, 48.349559], [-113.192346, 48.941153]]
        ],
        'AZT': [
            [[ -112.159124, 33.184167], [ -111.920172, 33.722682], [ -111.705938, 33.193361]],
            [[ -110.898443, 32.451605], [ -110.875784, 32.361460], [ -110.720259, 32.360009], [ -110.720259, 32.457109]]
        ],
        'PCT': [
            [[-122.173511, 40.819048], [-122.178234, 40.513852], [-121.740926, 40.490152], [-121.798541, 40.756833]],
            [[-121.607023, 47.532033], [-121.610801, 47.265432], [-121.193327, 47.356368]]
        ],
        'CDT': [
            [[ -108.067945, 45.055377],[-108.130315, 44.006080],[-106.443914, 44.057421],[-106.471379, 45.051626]],
            [[ -107.289151, 36.443293],[-106.684903, 37.168985],[-105.668668, 36.044569]]
        ]
    }

    def fill_test_fires(self, fires: List[List[List[float]]]) -> List[object]:
        test_fires = copy.deepcopy(self.test_fires_template)
        test_fires[0]['geometry']['rings'] = [fires[0]]
        test_fires[1]['geometry']['rings'] = [fires[1]]
        return test_fires
    
    def test_mile_markers(self) -> None:
        tracker = TestFireTracker(self.trail,  self.fill_test_fires(self.test_fires[self.trail]))
        mile_markers = list(tracker.trail_mile_markers.values())
        try:
            self.assertTrue(mile_markers[0] < 1)
            print(f'test_mile_markers PASSED: first mile marker expected size\n\n{mile_markers[0]} mi. to {mile_markers[len(mile_markers) - 1]} mi.')
        except AssertionError:
            print(f'test_mile_markers FAILED: first mile marker larger than expected size\n\n{mile_markers[0]} mi. to {mile_markers[len(mile_markers) - 1]} mi.')

    def test_add_fires(self) -> None:
        tracker = TestFireTracker(self.trail,  self.fill_test_fires(self.test_fires[self.trail]))
        tracker.plot()
        try:
            self.assertTrue(len(tracker.state_fires) == 2)
            print('.test_add_fires PASSED: test fires were added to state fires.')
        except AssertionError:
            print('test_add_fires FAILED: test fires were not added to state fires.')
    
    def test_fire_not_crossing_trail(self) -> None:
        tracker = TestFireTracker(self.trail,  self.fill_test_fires(self.test_fires[self.trail]))
        try:
            self.assertTrue(any(fire['attributes']['name'] == '🔥🔥🔥 NOT CROSSING TRAIL 🔥🔥🔥' and fire not in tracker.fires_crossing_trail for fire in tracker.state_fires))
            print('test_fire_not_crossing_trail PASSED: test fire was not crossing trail.')
        except AssertionError:
            print('test_fire_not_crossing_trail FAILED: test fire was crossing the trail.')

    def test_fire_crossing_trail(self) -> None:
        tracker = TestFireTracker(self.trail,  self.fill_test_fires(self.test_fires[self.trail]))
        try:
            self.assertTrue(any(fire['attributes']['name'] == '🔥🔥🔥 IS CROSSING TRAIL 🔥🔥🔥' for fire in tracker.fires_crossing_trail))
            print('test_fire_crossing_trail PASSED: test fire was crossing trail.')
        except AssertionError:
            print('test_fire_crossing_trail FAILED: test fire was not crossing the trail.')
    
    def test_sms(self) -> None:
        tracker = TestFireTracker(self.trail,  self.fill_test_fires(self.test_fires[self.trail]))
        try:
            self.assertTrue(tracker.create_SMS())
            print(f'test_sms PASSED: sms created\n\n{tracker.text}')
        except AssertionError:
            print('test_sms FAILED: sms not created')

if __name__ == '__main__':
    unittest.main()