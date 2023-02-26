import requests
import threading
import matplotlib.pyplot as plt
from typing import *
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import linemerge
import geopandas as gpd
import matplotlib.pyplot as plt
import gpxpy
from geopy import distance
from sklearn.neighbors import NearestNeighbors
from math import radians, cos, sin, asin, sqrt

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
if os.environ.get('mode') == 'dev':
    DEBUG = True
    DEVELOPMENT = True
    LISTEN_ADDRESS = '127.0.0.1'
    LISTEN_PORT = 5000
else:
    DEBUG = False
    TESTING = False
    LISTEN_ADDRESS = '209.94.59.175'
    LISTEN_PORT = 5000
            
class FireTracker():
    def __init__(self, trail: str) -> None:
        self.text = ''
        self.trail = trail
        self.trail_list = {
            'CT': {
                'states': ['Colorado'],
                'data': 'gpx_files/Colorado_Trail.gpx'
            },
            'PCT': {
                'states': ['California', 'Oregon', 'Washington'],
                'data': 'gpx_files/Pacific_Crest_Trail.gpx'
            },
            'CDT': {
                'states': ['New Mexico', 'Colorado', 'Wyoming', 'Idaho', 'Montana'],
                'data': 'gpx_files/Continental_Divide_Trail.gpx'
            },
            'PNT': {
                'states': ['Montana', 'Idaho', 'Washington'],
                'data': 'gpx_files/Pacific_Northwest_Trail.gpx'
            },
            'AZT': {
                'states': ['Arizona'],
                'data': 'gpx_files/Arizona_Trail.gpx'
            }
        }
        self.trail_linestring = self.get_trail_linestring(self.trail_list[trail]['data'])
        self.trail_mile_markers = self.get_mile_markers(self.trail_linestring)
        self.states = self.trail_list[trail]['states']
        self.state_border_polygons = [self.get_border(state) for state in self.states]
        self.state_fires = self.get_state_fires(self.state_border_polygons)
        self.fires_crossing_trail = self.get_fires_crossing_trail(self.trail_linestring, self.state_fires)
        self.closest_points = self.get_closest_points(self.trail_linestring, self.state_fires)
    
    def plot(self):
        y, x = self.trail_linestring.xy
        plt.plot(x, y, color='green')
        for fire in self.state_fires:
            y, x = fire['shape'].exterior.xy
            plt.fill(x, y, color='red')
        for border in self.state_border_polygons:
            x, y = border.exterior.xy
            plt.plot(x, y, color='grey')
        plt.axis('equal')
        plt.savefig(f'{self.trail}_fires.png')

    def call_fire_api(self) -> List[object]:
        api_url = 'https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Perimeters/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json'
        response = requests.get(api_url)
        data = response.json()
        return data['features']

    def getdistance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 3959.87433 # radius in miles
        dLat = radians(lat2 - lat1)
        dLon = radians(lon2 - lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return R * c

    # Finds closest point in a fire to the trail if not crossing
    def closest(self, trail_coords: List[List[float]], fire_coords: List[List[float]]) -> List[float]:
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

    # Retrieve state border data as a Shapely polygon
    def get_border(self, state: str) -> Polygon:
        borders = gpd.read_file('./state_borders/tl_2022_us_state.shp')
        borders = borders.to_crs(epsg=4326)
        borders = borders[['NAME', 'geometry']]
        borders = borders.set_index('NAME')
        state_border = borders.loc[state]
        if isinstance(state_border, gpd.GeoSeries):
            raise ValueError(f'State {state} has multiple borders')
        return state_border.geometry

    # Convert trail data to Shapely linestring
    def get_trail_linestring(self, filename: str) -> LineString:
        with open(filename, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        coords = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    coords.insert(0, (point.latitude, point.longitude))
        coords = self.remove_distant_points(coords)
        return LineString(coords)

    def remove_distant_points(self, coords):
        new_coords = []
        prev_lat, prev_lon = None, None
        for lat, lon in coords:
            if prev_lat is not None and prev_lon is not None:
                dist = distance.distance((prev_lat, prev_lon), (lat, lon)).miles
                if dist > 300:
                    continue  # Skip this point if it's more than 10 miles from the previous point
            new_coords.append((lat, lon))
            prev_lat, prev_lon = lat, lon
        return new_coords

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

    def is_in_state(self, coord: List[float], borders: List[Polygon]) -> bool:
        p = Point(coord[1], coord[0])
        return any(border.contains(p) for border in borders)

    def get_state_fires(self, borders: List[Polygon]) -> List[object]:
        current_fires = self.call_fire_api()
        state_fires = []
        for fire in current_fires:
            coords = self.switch_xy(fire['geometry']['rings'][0])
            for coord in coords:
                if self.is_in_state(coord, borders):
                    state_fires.append({
                        'attributes': {
                            'name': fire['attributes']['irwin_IncidentName'],
                            'acres': fire['attributes']['poly_GISAcres'],
                            'containment': fire['attributes']['irwin_PercentContained']
                        },
                        'shape': Polygon(coords)
                    })
                    break
        return state_fires

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
        
    def get_closest_points(self, trail: LineString, fires: List[object]) -> List[object]:
        closest_points = []
        trail_coords = list(trail.coords)
        for fire in fires:
            fire_coords = list(fire['shape'].exterior.coords)
            distancebetween = []
            for i in range(len(fire_coords) - 1):
                distancebetween.append(self.getdistance(fire_coords[i][0], fire_coords[i][1], fire_coords[i+1][0], fire_coords[i+1][1]))
            low_res_trail = self.reduce_if_greater(trail_coords, 2000)
            low_res_fire = self.reduce_if_greater(fire_coords, 5000)
            closest_points.append(self.closest(low_res_trail, low_res_fire))
        return closest_points
        # closest_points = list of {
        #     'distance': d,
        #     'fire_coord': fire_coord,
        #     'trail_coord': trail_coord
        # } for each fire
    
    def text_add_state_fires(self) -> None:
        text = ''
        text += f"Total fires in {', '.join(self.states)}: {len(self.state_fires)}\n"
        for fire in self.state_fires:
            attributes = fire['attributes']
            text += f"{attributes['name']} Fire"
            area = round(attributes['acres'])
            containment = round(attributes['containment'])
            if area or containment: text += ' - '
            if area:
                text += str(area) + ' acres'
                if containment: text += ', '
            if containment:
                text += str(containment) + '% contained'
            text += '\n'
        self.text += text

    def text_add_fires_crossing_trail(self) -> None:
        text = ''
        text += f'\n{len(self.fires_crossing_trail)} fire(s) currently cross the {self.trail}\n'
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

    def create_SMS(self):
        self.text_add_state_fires()
        self.text_add_fires_crossing_trail()

# ct = FireTracker('CT')
# ct.create_SMS()
# print(ct.text)


# @app.route('/sms', methods=['POST'])

# def sms_reply():
#     resp = MessagingResponse()
#     resp.message(text)
#     return str(resp)

# if __name__ == '__main__':
#     app.run(host = LISTEN_ADDRESS, port = LISTEN_PORT)

# # TO DO :
# # refactor
# # create test fire data to check refactoring
# # assemble trail data 