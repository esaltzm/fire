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

def callAPI():
    api_url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Perimeters/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
    response = requests.get(api_url)
    all = response.json()
    fires = all['features']
    return fires

# distance formula

def getdistance(lat1, lon1, lat2, lon2):

      R = 3959.87433 # this is in miles
      dLat = radians(lat2 - lat1)
      dLon = radians(lon2 - lon1)
      lat1 = radians(lat1)
      lat2 = radians(lat2)
      a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
      c = 2*asin(sqrt(a))
      return R * c

# Alternative method of finding closest points

def closest(fire, ctcoords):
    comparisons = []
    for coords in fire:
        for latlong in ctcoords:
            d = getdistance(coords[1],coords[0],latlong[0],latlong[1])
            comparisons.append([d,coords,latlong])
    comparisons.sort()
    return comparisons[0]

def approx(loc, diclist):
    least_dist = 10000000
    closest_point = (0,0)
    for latlong in diclist:
        d = getdistance(loc[0],loc[1],latlong[0],latlong[1])
        if d < least_dist:
            least_dist = d
            closest_point = latlong
    return closest_point

# Method of finding approximate mile marker when none match

def closest_node(node, nodes):
    nodes = np.asarray(nodes)
    deltas = nodes - node
    dist_2 = np.einsum('ij,ij->i', deltas, deltas)
    return np.argmin(dist_2)

# Retrieve state border data as a Shapely object

def get_borders(state):
    borders = gpd.read_file('./state_borders/tl_2022_us_state.shp')
    borders = borders.to_crs(epsg=4326)
    borders = borders[['NAME', 'geometry']]
    borders = borders.set_index('NAME')
    state_border = borders.loc[state]
    if isinstance(state_border, gpd.GeoSeries):
        raise ValueError(f"State '{state}' has multiple borders, please use get_borders_list() instead.")
    return state_border.geometry

# Retrieve trail data as Shapely linestring

def get_trail_linestring(trail, trail_list):
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

def get_mile_markers(linestring):
    milemarkers = {}
    distance = 0
    coords = list(linestring.coords)
    for i in range(1, len(coords)):
        current_distance = getdistance(coords[i-1][0],coords[i-1][1],coords[i][0],coords[i][1])
        milemarkers[coords[i]] = distance + current_distance
        distance += current_distance
    return milemarkers

def in_state(coord, state_border_polygons):
    p = Point(coord[1], coord[0])
    return any(state.contains(p) for state in state_border_polygons)


def get_current_fires(state_border_polygons):
    fires = callAPI()
    current_fires = []
    for fire in fires:
        fire_in_state = False
        listofcoords = []
        for key in fire:
            coords = fire['geometry']['rings']
            for coordlist in coords:
                for coord in coordlist:
                    if in_state(coord, state_border_polygons):
                        listofcoords.append(coord)
                        fire_in_state = True
        if fire_in_state == True:
            current_fires.append({
                "fire": fire,
                "shape": Polygon(listofcoords)
            })
    return current_fires

def switch_xy(points):
    for i in range(len(points)):
        item = list(points[i])
        temp = item[0]
        item[0] = item[1]
        item[1] = temp
        points[i] = tuple(item)
    return points

def get_fires_crossing_trail(trail_linestring, current_fires):
    fires_crossing_trail = []
    for fire in current_fires:
        if trail_linestring.intersects(fire["shape"]):
            fires_crossing_trail.append(fire)
    return fires_crossing_trail

def get_closest_points(trail_linestring, current_fires):
    closest_points = []
    coords = list(trail_linestring.coords)
    for fire in current_fires:
        fire_shape = fire["shape"]
        distancebetween = []
        for i in range(len(fire_shape)-1):
            distancebetween.append(getdistance(fire_shape[i][0],fire_shape[i][1],fire_shape[i+1][0],fire_shape[i+1][1]))
        reducefactor = round(0.1/(sum(distancebetween)/len(distancebetween)))
        lowresct = []
        lowresfire = []
        if(reducefactor > 0):
            for k in range(0,len(fire_shape),reducefactor):
                lowresfire.append(fire_shape[k])
        else:
            for k in range(len(fire_shape)):
                lowresfire.append(fire_shape[k])
        for l in range(0,len(coords),2):
            lowresct.append(coords[l])
        closest_points.append(closest(lowresfire,lowresct))
    return closest_points
            
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
        self.trail_linestring = get_trail_linestring(trail, self.trail_list)
        self.trail_mile_markers = get_mile_markers(self.trail_linestring)
        self.states = self.trail_list[trail]['states']
        self.state_border_polygons = [get_borders(state) for state in self.states]
        self.current_fires = get_current_fires(self.state_border_polygons)
        self.fires_crossing_trail = get_fires_crossing_trail(self.trail_linestring, self.current_fires)
        self.closest_points = get_closest_points(self.trail_linestring, self.current_fires)
    def create_SMS(self):
        self.text += f"Total fires in {', '.join(self.states)}: {len(self.current_fires)}\n"
        for fire in self.current_fires:
            self.text += f"{str(fire['fire']['attributes']['irwin_IncidentName'])} Fire"
            area = round(fire['fire']['attributes']['poly_GISAcres'])
            containment = round(fire['fire']['attributes']['irwin_PercentContained'])
            if area or containment: self.text += ' - '
            if area:
                self.text += str(area) + " acres"
                if containment: self.text += ", "
            if containment:
                text += str(containment) + "%% contained"

            text += f"\n{len(self.fires_crossing_trail)} fires currently cross the {self.trail}\n"
            for fire in self.fires_crossing_trail:
                cross_points = list(self.trail_linestring.intersection(fire['shape']).coords)
                start = tuple(switch_xy(list(cross_points[0])))
                end = tuple(switch_xy(list(cross_points[len(cross_points)-1])))
                startmi = self.trail_mile_markers[approx(start,list(self.trail_mile_markers.keys()))]
                endmi = self.trail_mile_markers[approx(end,list(self.trail_mile_markers.keys()))]
                text += f"The {fire['fire']['attributes']['irwin_IncidentName']} Fire crosses the {self.trail} at mi. {round(startmi)}"
                if(abs(endmi - startmi) > 1):
                    text += f" to mi. {round(endmi)}"
                text += "\n"

ct = FireTracker('CT')
ct.create_SMS()
print(ct.text)


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