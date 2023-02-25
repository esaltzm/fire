import unittest
from firetracker import FireTracker
from shapely.geometry import LineString, Polygon, Point


class TestFireTracker(FireTracker):
    def __init__(self, trail, test_fire):
        super().__init__(trail)
        self.state_fires = [test_fire]
        self.fires_crossing_trail = self.get_fires_crossing_trail(self.trail_linestring, self.state_fires)
        self.closest_points = self.get_closest_points(self.trail_linestring, self.state_fires)

class FireUnitTesting(unittest.TestCase):

    test_fire = {
        'attributes': {
            'poly_GISAcres': 50,
            'irwin_IncidentName': '🔥🔥🔥 TEST FIRE 🔥🔥🔥',
            'irwin_PercentContained': 95,
        },
        'shape': Polygon([(38.070289, -107.460916), (38.070289, 107.556031), (38.135239, -107.556031), (38.135239, -107.460916)])
    }

    def test_add_fire(self):
        tracker = TestFireTracker('CT', self.test_fire)
        try:
            self.assertTrue(any(fire.get('attributes', {}).get('irwin_IncidentName') == '🔥🔥🔥 TEST FIRE 🔥🔥🔥' for fire in tracker.state_fires))
            print('Test passed: test fire was added to state fires.')
        except AssertionError:
            print('Test failed: test fire was not added to state fires.')
    
    # def test_fire_not_crossing_trail(self):
    #     tracker = TestFireTracker('CT', self.test_fire)
    #     try:
    #         self.assertTrue(any(fire.get('attributes', {}).get('irwin_IncidentName') == '🔥🔥🔥 TEST FIRE 🔥🔥🔥' for fire in tracker.state_fires))
    #         print('Test passed: test fire was added to state fires.')
    #     except AssertionError:
    #         print('Test failed: test fire was not added to state fires.')

if __name__ == '__main__':
    test_case = FireUnitTesting()
    unittest.main()