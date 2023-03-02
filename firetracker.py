import requests
import traceback
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.pyplot as plt
import gpxpy
from typing import *
from shapely.geometry import LineString, Polygon, Point, MultiPolygon
from math import radians, cos, sin, asin, sqrt
            
class FireTracker():
    def __init__(self, trail: str, current_fires: List[object]) -> None:
        self.current_fires = current_fires
        self.text = ''
        self.trail = trail
        self.trail_list = { # 'states' includes states within 50 miles of trail
            'CT': {
                'name': 'Colorado Trail',
                'states': ['Colorado', 'New Mexico'],
                'data': 'gpx_files/Colorado_Trail.gpx'
            },
            'PCT': {
                'name': 'Pacific Crest Trail',
                'states': ['California', 'Nevada', 'Oregon', 'Washington'],
                'data': 'gpx_files/Pacific_Crest_Trail.gpx'
            },
            'CDT': {
                'name': 'Continental Divide Trail',
                'states': ['Arizona', 'New Mexico', 'Colorado', 'Wyoming', 'Idaho', 'Montana'],
                'data': 'gpx_files/Continental_Divide_Trail.gpx'
            },
            'PNT': {
                'name': 'Pacific Northwest Trail',
                'states': ['Montana', 'Idaho', 'Washington'],
                'data': 'gpx_files/Pacific_Northwest_Trail.gpx'
            },
            'AZT': {
                'name': 'Arizona Trail',
                'states': ['Arizona', 'Utah'],
                'data': 'gpx_files/Arizona_Trail.gpx'
            }
        }
        self.trail_linestring = self.get_trail_linestring(self.trail_list[trail]['data'])
        self.trail_buffer = self.get_trail_buffer(self.trail_linestring)
        self.trail_mile_markers = self.get_mile_markers(self.trail_linestring)
        self.states = self.trail_list[trail]['states']
        self.state_border_polygons = [self.get_border(state) for state in self.states]
        self.close_fires = self.get_close_fires(self.trail_buffer, self.current_fires)
        self.fires_crossing_trail = self.get_fires_crossing_trail(self.trail_linestring, self.close_fires)
        self.closest_points = self.get_closest_points(self.trail_linestring, self.close_fires)
    
    def plot(self) -> None:
        # plt.clf()
        for border in self.state_border_polygons:
            x, y = border['border'].exterior.xy
            plt.plot(x, y, color='grey')
        y, x = self.trail_linestring.xy
        plt.plot(x, y, color='green')
        y, x = self.trail_buffer.exterior.xy
        plt.plot(x, y, color='blue')
        for fire in self.close_fires:
            y, x = fire['shape'].exterior.xy
            plt.fill(x, y, color='red')
            centroid = fire['shape'].centroid
            plt.text(centroid.y + 1, centroid.x, fire['attributes']['name'])
        plt.axis('equal')
        plt.savefig(f'{self.trail}_fires.png')

    def getdistance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 3959.87433 # radius in miles
        dLat = radians(lat2 - lat1)
        dLon = radians(lon2 - lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return R * c

    # Finds closest mile marker to an intersection of the trail and a fire perimeter
    def approx_mile_marker(self, intersection: List[float], trail_coords: List[List[float]]) -> List[float]:
        least_dist = float('inf')
        closest_point = [0,0]
        for trail_coord in trail_coords:
            d = self.getdistance(intersection[0],intersection[1],trail_coord[0],trail_coord[1])
            if d < least_dist:
                least_dist = d
                closest_point = trail_coord
        return closest_point
    
    # Used to reduce state with multiple borders (ex. California with islands) to just main state border
    def get_largest_polygon(self, multipolygon: List[Polygon]) -> Polygon:
        largest_area = 0
        largest_polygon = None
        for polygon in multipolygon:
            if isinstance(polygon, Polygon):
                area = polygon.area
                if area > largest_area:
                    largest_area = area
                    largest_polygon = polygon
        return largest_polygon

    # Retrieve state border data as a Shapely polygon
    def get_border(self, state: str) -> object:
        borders = gpd.read_file('./state_borders/tl_2022_us_state.shp')
        borders = borders.to_crs(epsg=4326)
        borders = borders[['NAME', 'geometry']]
        borders = borders.set_index('NAME')
        state_border = borders.loc[state]
        polygon = state_border.geometry
        if isinstance(polygon, MultiPolygon):
            polygon = self.get_largest_polygon(polygon.geoms)
        return {
            'state': state,
            'border': polygon
        }

    # Convert trail data to Shapely linestring
    def get_trail_linestring(self, filename: str) -> LineString:
        with open(filename, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        coords = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    coords.insert(0, (point.latitude, point.longitude))
        if self.trail in ['AZT', 'PNT', 'PCT']: coords.reverse()
        return LineString(coords)

    def get_trail_buffer(self, trail: LineString) -> Polygon:
        return trail.buffer(50/69) # Approximate degrees per 50 mile radius
    
    # Create mile markers for each point in CT in the format dictionary[coordinate pair] = mile marker
    def get_mile_markers(self, trail: LineString) -> dict:
        mile_markers = {}
        distance = 0
        coords = list(trail.coords)
        for i in range(1, len(coords)):
            current_distance = self.getdistance(coords[i-1][0],coords[i-1][1],coords[i][0],coords[i][1])
            mile_markers[coords[i]] = distance + current_distance
            distance += current_distance
        return mile_markers

    def is_in_state(self, fire: Polygon, border: Polygon) -> bool:
        for coord in fire.exterior.coords:
            p = Point(coord[1], coord[0])
            if border.contains(p): return True
        return False
    
    def get_close_fires(self, buffer: Polygon, current_fires: List[object]) -> List[object]:
        close_fires = []
        for fire in current_fires:
            fire_shape = Polygon(self.switch_xy(fire['geometry']['rings'][0]))
            if fire_shape.overlaps(buffer) or fire_shape.intersects(buffer):
                states = [] # catch case of multi-state fire
                for state_border in self.state_border_polygons:
                    if self.is_in_state(fire_shape, state_border['border']):
                        states.append(state_border['state'])
                if len(states) == 0: states = ['Non U.S.']
                close_fires.append({
                    'attributes': {
                        'name': fire['attributes']['irwin_IncidentName'],
                        'states': states,
                        'acres': fire['attributes']['poly_GISAcres'],
                        'containment': fire['attributes']['irwin_PercentContained']
                    },
                    'shape': fire_shape
                })
        return close_fires

    def switch_xy(self, points: List[List[float]]) -> List[List[float]]:
        for point in points:
            temp = point[0]
            point[0] = point[1]
            point[1] = temp
        return points

    def get_fires_crossing_trail(self, trail: LineString, fires: List[object]) -> List[object]:
        fires_crossing_trail = []
        for fire in fires:
            if trail.intersects(fire['shape']):
                intersection = trail.intersection(fire['shape'])
                if intersection.geom_type == 'LineString':
                    cross_points = list(intersection.coords) 
                else: #MultiLineString
                    cross_points = []
                    for line in intersection.geoms:
                        for coord in line.coords:
                            cross_points.append(coord)
                fire['intersection'] = cross_points
                fires_crossing_trail.append(fire)
        return fires_crossing_trail
    
    # Reduce list size if too big (for purposes of comparing all list points to find closest pairing)
    def reduce_if_greater(self, arr: List, n: int) -> List:
        if len(arr) <= n: return arr
        low_res = []
        for i in range(0, len(arr), len(arr) // n):
            low_res.append(arr[i])
            if len(low_res) == n:
                break
        return low_res

    # Finds closest point in a fire to the trail if not crossing
    def closest_point(self, trail_coords: List[List[float]], fire_coords: List[List[float]]) -> List[float]:
        comparisons = []
        for fire_coord in fire_coords:
            for trail_coord in trail_coords:
                d = self.getdistance(fire_coord[0],fire_coord[1],trail_coord[0],trail_coord[1])
                comparisons.append({
                    'distance': d,
                    'fire_coord': fire_coord,
                    'trail_coord': trail_coord
                })
        return sorted(comparisons, key=lambda x: x['distance'])[0]
        
    def get_closest_points(self, trail: LineString, fires: List[object]) -> List[object]:
        closest_points = []
        trail_coords = list(trail.coords)
        for fire in fires:
            if not trail.intersects(fire['shape']):
                fire_coords = list(fire['shape'].exterior.coords)
                low_res_trail = self.reduce_if_greater(trail_coords, 2000)
                low_res_fire = self.reduce_if_greater(fire_coords, 5000)
                closest_point = self.closest_point(low_res_trail, low_res_fire)
                closest_point['name'] = fire['attributes']['name']
                closest_points.append(closest_point)
        return closest_points
        # closest_points = list of {
        #     'name': fire['attributes']['name']
        #     'distance': d,
        #     'fire_coord': fire_coord,
        #     'trail_coord': trail_coord
        # } for each fire
    
    def text_add_close_fires(self) -> None:
        text = ''
        text += f"Total fires within 50 miles of the {self.trail}: {len(self.close_fires)}\n"
        for fire in self.close_fires:
            attributes = fire['attributes']
            states = attributes['states']
            text += f"{attributes['name']} Fire ({states[0] if len(states) == 1 else ', '.join(states[:-1]) + ' and ' + states[-1]})"
            area = attributes['acres']
            containment = attributes['containment']
            if area or containment: text += ' - '
            if area:
                text += str(round(area)) + ' acres'
                if containment: text += ', '
            if containment:
                text += str(round(containment)) + '% contained'
            text += '\n'
        self.text += text
    
    def text_add_closest_points(self) -> None:
        text = '\n'
        for point in self.closest_points:
            mile_marker = self.trail_mile_markers[self.approx_mile_marker(point['trail_coord'],list(self.trail_mile_markers.keys()))]
            text += f"The {point['name']} Fire is {round(point['distance'])} mi. from the {self.trail} at mile marker {round(mile_marker)}\n"
        self.text += text

    def text_add_fires_crossing_trail(self) -> None:
        text = '\n'
        text += f'{len(self.fires_crossing_trail)} fire(s) currently cross the {self.trail}\n'
        for fire in self.fires_crossing_trail:
            cross_points = fire['intersection']
            start = cross_points[0]
            end = cross_points[len(cross_points) - 1]
            start_mile = self.trail_mile_markers[self.approx_mile_marker(start,list(self.trail_mile_markers.keys()))]
            end_mile = self.trail_mile_markers[self.approx_mile_marker(end,list(self.trail_mile_markers.keys()))]
            text += f"The {fire['attributes']['name']} Fire crosses the {self.trail} at mi. {round(start_mile)}"
            if(abs(end_mile - start_mile) > 1):
                text += f' to mi. {round(end_mile)}'
            text += '\n'
        self.text += text

    def create_SMS(self) -> bool:
        try:
            self.text_add_close_fires()
            self.text_add_closest_points()
            self.text_add_fires_crossing_trail()
            return True
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            return False
