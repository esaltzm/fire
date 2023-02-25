import requests
import threading
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Polygon, Point
import geopandas as gpd
from math import radians, cos, sin, asin, sqrt

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
if os.environ.get('mode') == "dev":
    DEBUG = True
    DEVELOPMENT = True
    LISTEN_ADDRESS = "127.0.0.1"
    LISTEN_PORT = 5000
else:
    DEBUG = False
    TESTING = False
    LISTEN_ADDRESS = "209.94.59.175"
    LISTEN_PORT = 5000
            
class FireTracker():
    def __init__(self, trail):
        self.text = ""
        self.trail = trail
        self.trail_list = {
            "CT": {
                "states": ["Colorado"],
                "data": "ct.txt"
            },
            "PCT": {
                "states": ["California", "Oregon", "Washington"],
                "data": None
            },
            "CDT": {
                "states": ["New Mexico", "Colorado", "Wyoming", "Idaho", "Montana"],
                "data": None
            },
            "PNT": {
                "states": ["Montana", "Idaho", "Washington"],
                "data": None
            },
            "AZT": {
                "states": ["Arizona"],
                "data": None
            }
        }
        self.trail_linestring = self.get_trail_linestring(trail, self.trail_list)
        self.trail_mile_markers = self.get_mile_markers(self.trail_linestring)
        self.states = self.trail_list[trail]['states']
        self.state_border_polygons = [self.get_borders(state) for state in self.states]
        self.state_fires = self.get_state_fires(self.state_border_polygons)
        self.fires_crossing_trail = self.get_fires_crossing_trail(self.trail_linestring, self.state_fires)
        self.closest_points = self.get_closest_points(self.trail_linestring, self.state_fires)

    def call_fire_api(self):
        api_url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Perimeters/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
        response = requests.get(api_url)
        data = response.json()
        return data['features']

    def getdistance(self, lat1, lon1, lat2, lon2):

        R = 3959.87433 # radius in miles
        dLat = radians(lat2 - lat1)
        dLon = radians(lon2 - lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return R * c

    # Finds closest point in a fire to 
    def closest(self, trail_coords, fire_coords): # takes fire shape coordinate list, trail coord list
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

    def approx(self, loc, diclist):
        least_dist = 10000000
        closest_point = (0,0)
        for latlong in diclist:
            d = self.getdistance(loc[0],loc[1],latlong[0],latlong[1])
            if d < least_dist:
                least_dist = d
                closest_point = latlong
        return closest_point

    # Retrieve state border data as a Shapely object

    def get_borders(self, state):
        borders = gpd.read_file('./state_borders/tl_2022_us_state.shp')
        borders = borders.to_crs(epsg=4326)
        borders = borders[['NAME', 'geometry']]
        borders = borders.set_index('NAME')
        state_border = borders.loc[state]
        if isinstance(state_border, gpd.GeoSeries):
            raise ValueError(f"State '{state}' has multiple borders")
        return state_border.geometry

    # Retrieve trail data as Shapely linestring

    def get_trail_linestring(self, trail, trail_list):
        gpx = open(trail_list[trail]['data'], 'r')
        line = gpx.readline()
        coords = []
        while line:
            coord = line.split("\t")
            if len(coord) == 5:
                coords.append((coord[2], coord[3]))
            line = gpx.readline()
        gpx.close()
        return LineString(coords)

    # Create mile markers for each point in CT, dictionary[coordinate pair] = mile marker

    def get_mile_markers(self, linestring):
        milemarkers = {}
        distance = 0
        coords = list(linestring.coords)
        for i in range(1, len(coords)):
            current_distance = self.getdistance(coords[i-1][0],coords[i-1][1],coords[i][0],coords[i][1])
            milemarkers[coords[i]] = distance + current_distance
            distance += current_distance
        return milemarkers

    def is_in_state(self, coord, state_border_polygons):
        # print('coord', coord, 'state_border_polygons', state_border_polygons)
        p = Point(coord[1], coord[0])
        return any(state.contains(p) for state in state_border_polygons)

    def get_state_fires(self, state_border_polygons):
        current_fires = self.call_fire_api()
        state_fires = []
        for fire in current_fires:
            in_state = False
            listofcoords = []
            coords = self.switch_xy(fire['geometry']['rings'][0])
            for coord in coords:
                if self.is_in_state(coord, state_border_polygons):
                    listofcoords.append(coord)
                    in_state = True
            if in_state == True:
                state_fires.append({
                    "attributes": {
                        "name": fire['attributes']['irwin_IncidentName'],
                        "acres": fire['attributes']['poly_GISAcres'],
                        "containment": fire['attributes']['irwin_PercentContained']
                    },
                    "shape": Polygon(listofcoords)
                })
        return state_fires

    def switch_xy(self, points):
        for point in points:
            temp = point[0]
            point[0] = point[1]
            point[1] = temp
        return points

    def get_fires_crossing_trail(self, trail_linestring, state_fires):
        fires_crossing_trail = []
        for fire in state_fires:
            if trail_linestring.intersects(fire["shape"]):
                fires_crossing_trail.append(fire)
        return fires_crossing_trail
    
    # Reduce list size if too big (for purposes of comparing all list points to find closest pairing)
    def reduce_if_greater(self, arr, n):
        if len(arr) <= n: return arr
        low_res = []
        for i in range(0, len(arr), len(arr) // n):
            low_res.append(arr[i])
            if len(low_res) == n:
                break
        return low_res
        
    def get_closest_points(self, trail_linestring, state_fires):
        closest_points = []
        trail_coords = list(trail_linestring.coords)
        for fire in state_fires:
            fire_coords = list(fire['shape'].exterior.coords)
            distancebetween = []
            for i in range(len(fire_coords) - 1):
                distancebetween.append(self.getdistance(fire_coords[i][0], fire_coords[i][1], fire_coords[i+1][0], fire_coords[i+1][1]))
            low_res_trail = self.reduce_if_greater(trail_coords, 2000)
            low_res_fire = self.reduce_if_greater(fire_coords, 5000)
            closest_points.append(self.closest(low_res_trail, low_res_fire))
        return closest_points
        # closest_points = arr of {
        #     'distance': d,
        #     'fire_coord': fire_coord,
        #     'trail_coord': trail_coord
        # } for each fire
    
    def text_add_state_fires(self):
        text = ''
        text += f"Total fires in {', '.join(self.states)}: {len(self.state_fires)}\n"
        for fire in self.state_fires:
            attributes = fire['attributes']
            text += f"{attributes['name']} Fire"
            area = round(attributes['acres'])
            containment = round(attributes['containment'])
            if area or containment: text += ' - '
            if area:
                text += str(area) + " acres"
                if containment: text += ", "
            if containment:
                text += str(containment) + "%% contained"
        self.text += text

    def text_add_fires_crossing_trail(self):
        text = ''
        text += f"\n{len(self.fires_crossing_trail)} fires currently cross the {self.trail}\n"
        for fire in self.fires_crossing_trail:
            cross_points = list(self.trail_linestring.intersection(fire['shape']).coords)
            start = tuple(self.switch_xy(list(cross_points[0])))
            end = tuple(self.switch_xy(list(cross_points[len(cross_points)-1])))
            startmi = self.trail_mile_markers[self.approx(start,list(self.trail_mile_markers.keys()))]
            endmi = self.trail_mile_markers[self.approx(end,list(self.trail_mile_markers.keys()))]
            text += f"The {fire['attributes']['name']} Fire crosses the {self.trail} at mi. {round(startmi)}"
            if(abs(endmi - startmi) > 1):
                text += f" to mi. {round(endmi)}"
            text += "\n"
        self.text += text

    def create_SMS(self):
        self.text_add_state_fires()
        self.text_add_fires_crossing_trail()

# ct = FireTracker('CT')
# ct.create_SMS()
# print(ct.text)


# @app.route("/sms", methods=['POST'])

# def sms_reply():
#     resp = MessagingResponse()
#     resp.message(text)
#     return str(resp)

# if __name__ == "__main__":
#     app.run(host = LISTEN_ADDRESS, port = LISTEN_PORT)

# # TO DO :
# # refactor
# # create test fire data to check refactoring
# # assemble trail data 