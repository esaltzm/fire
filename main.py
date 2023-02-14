import requests
import threading
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Polygon, Multipolygon, Point
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
    comparisons = []
    for latlong in diclist:
        d = getdistance(loc[0],loc[1],latlong[0],latlong[1])
        comparisons.append([d,coords,latlong])
    comparisons.sort()
    return comparisons[0][2]

# Method of finding approximate mile marker when none match

def closest_node(node, nodes):
    nodes = np.asarray(nodes)
    deltas = nodes - node
    dist_2 = np.einsum('ij,ij->i', deltas, deltas)
    return np.argmin(dist_2)

# Retrieve state border data as a Shapely object

def get_borders(state):
    borders = gpd.read_file('./state_outlines/tl_2022_us_state')
    borders = borders.to_crs(epsg=4326)
    borders = borders[['NAME', 'geometry']]
    borders = borders.set_index('NAME')
    return borders.loc[state]

# Retrieve trail data as Shapely linestring

def get_trail_linestring(trail):
    gpx = open(trail , 'r')
    line = gpx.readline()
    coords = []
    while line:
        coords = line.split("\t")
        if(len(coords) == 5):
            del coords[0:2]
            del coords[2]
            latlong = []
            for coord in coords:
                latlong.append(float(coord))
            coords.append(tuple(latlong))
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
    current_fires = {
        "fires": [],
        "fire_shapes": []
    }
    for fire in fires:
        in_state = False
        listofcoords = []
        for key in fire:
            coords = fire['geometry']['rings']
            for coordlist in coords:
                for coord in coordlist:
                    if(in_state(coord, state_border_polygons)):
                        listofcoords.append(coord)
                        in_state = True
        if in_state == True:
            current_fires["fires"].append(fire)
            current_fires["fire_shapes"].append(Polygon(listofcoords))
    return current_fires

def switch_xy(linestring):
    coordlist = list(linestring.coords)
    for i in range(len(coordlist)):
        item = list(coordlist[i])
        temp = item[0]
        item[0] = item[1]
        item[1] = temp
        coordlist[i] = tuple(item)
    return LineString(coordlist)

def get_fires_crossing_trail(trail_linestring, current_fires):
    reversed_linestring = switch_xy(trail_linestring)
    cross = False
    ncross = 0
    for fire_shape in current_fires["fire_shapes"]:
        if trail_linestring.intersects(fire_shape):
            cross_points = list(trail_linestring.intersection(fire_shape).coords)
            start = crosslist[0]
            end = crosslist[len(crosslist)-1]
            startlist = list(start)
            endlist = list(end)
            temp = startlist[0]
            startlist[0] = startlist[1]
            startlist[1] = temp
            start = tuple(startlist)
            temp = endlist[0]
            endlist[0] = endlist[1]
            endlist[1] = temp
            end = tuple(endlist)
            startmi = milemarkers[approx(start,list(milemarkers.keys()))]
            endmi = milemarkers[approx(end,list(milemarkers.keys()))]
            text += "The "
            text += str(cofires[i]['attributes']['irwin_IncidentName'])
            text += " Fire crosses the CT at mi. "
            text += str(round(startmi))
            if(abs(endmi - startmi) > 1):
                text += " to mi. "
                text += str(round(endmi))
            text += "\n"
            del cofireshapes[i]
            del cofires[i]

# trail_list object specifies list of states for each trail + location of trail data

trail_list = {
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
    }
}

class FireTracker():
    def __init__(self, trail):
        self.text = ""
        self.trail = trail
        self.trail_linestring = get_trail_linestring(trail)
        self.trail_mile_markers = get_mile_markers(self.trail_linestring)
        self.states = trail_list[trail]
        self.state_border_polygons = list(map(get_borders, self.states))
        self.current_fires = get_current_fires(self.state_border_polygons)
    def create_SMS(self):
        self.text += f"Total fires in {', '.join(self.states)}: {self.current_fires}\n"
        for fire in self.current_fires:
            self.text += f"{str(fire['attributes']['irwin_IncidentName'])} Fire"
            area = round(fire['attributes']['poly_GISAcres'])
            containment = round(fire['attributes']['irwin_PercentContained'])
            if area or containment: self.text += ' - '
            if area:
                self.text += str(area) + " acres"
                if containment: self.text += ", "
            if containment:
                text += str(containment) + "%% contained"

def main():

    threading.Timer(3600, main).start()

    # Check if any fires cross the trail


    if cross == False:
        text += "0 fires cross the CT\n"
    if cross == True:
        text += str(ncross)
        text += " fires cross the CT\n"

    # If fires do not cross the trail, find their closest point to the trail

    closestpoints = []
    for i in range(len(cofireshapes)):
        distancebetween = []
        for j in range(len(cofireshapes[i])-1):
            distancebetween.append(getdistance(cofireshapes[i][j][0],cofireshapes[i][j][1],cofireshapes[i][j+1][0],cofireshapes[i][j+1][1]))
        reducefactor = round(0.1/(sum(distancebetween)/len(distancebetween)))
        lowresct = []
        lowresfire = []
        lowrescw = []
        if(reducefactor > 0):
            for k in range(0,len(cofireshapes[i]),reducefactor):
                lowresfire.append(cofireshapes[i][k])
        else:
            for k in range(len(cofireshapes[i])):
                lowresfire.append(cofireshapes[i][k])
        for l in range(0,len(ctcoords),2):
            lowresct.append(ctcoords[l])
        for m in range(0,len(cwcoords),2):
            lowrescw.append(cwcoords[m])
        closestpoints.append([closest(lowresfire,lowresct),closest(lowresfire,lowrescw)])

    # show line from fire to closest point on trail

    for i in range(len(closestpoints)):
        for j in range(len(closestpoints[i])):
            fireline = []
            fireline.append(tuple(closestpoints[i][j][1]))
            swap = []
            swap.append(closestpoints[i][j][2][1])
            swap.append(closestpoints[i][j][2][0])
            fireline.append(tuple(swap))
            fl = LineString(fireline)
            x,y = fl.xy
            plt.plot(x,y,linestyle = 'dotted', color = "red")

    for i in range(len(closestpoints)):
        if(closestpoints[i][0][0] < 50):
            text += str(cofires[i]['attributes']['irwin_IncidentName'])
            text += " Fire: "
            text += str(round(closestpoints[i][0][0],1))
            text += "mi from CT @ mi "
            text += str(round(milemarkers[closestpoints[i][0][2]],1))
            if(closestpoints[i][1][0] < 50):
                text += " and "
                text += str(round(closestpoints[i][1][0],1))
                text += "mi from CW alt @ mi "
                text += str(round(cwmilemarkers[closestpoints[i][1][2]],1))
        elif(closestpoints[i][1][0] < 50):
            text += str(cofires[i]['attributes']['irwin_IncidentName'])
            text += " Fire is: "
            text += str(round(closestpoints[i][1][0],1))
            text += "mi from CW alt @ mi "
            text += str(round(cwmilemarkers[closestpoints[i][1][2]],1))
        text += "\n"
    
    return text

# Save visuals

# plt.savefig("fire.png", dpi = 200)

text = main()
print(text)

#app = Flask(__name__)
@app.route("/sms", methods=['POST'])

def sms_reply():
    resp = MessagingResponse()
    resp.message(text)
    return str(resp)

if __name__ == "__main__":
    app.run(host = LISTEN_ADDRESS, port = LISTEN_PORT)

