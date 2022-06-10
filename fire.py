import requests
import shapely
import math
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point, LineString, Polygon, MultiPoint
from shapely.ops import nearest_points
from math import radians, cos, sin, asin, sqrt

import os
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)
if(os.environ['mode'] == "dev"):
    DEBUG = True
    DEVELOPMENT = True
    LISTEN_ADDRESS = "127.0.0.1"
    LISTEN_PORT = 5000
else:
    DEBUG = False
    TESTING = False
    LISTEN_ADDRESS = "209.94.59.175"
    LISTEN_PORT = 5000

#distance formula

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

# Creating border of Colorado

colorado = [(-102.05, 37), (-102.05, 41), (-109.05, 41), (-109.05, 37)]
co = Polygon(colorado)
x,y = co.exterior.xy
#plt.plot(x,y)

# Reading and creating line from Colorado Trail gpx file

ctgpx = open('ct.txt' , 'r')
line = ctgpx.readline()
ctcoords = [(39.490350000, -105.095165000)]
count = 0
while line:
    coords = line.split("\t")
    if(len(coords) == 5):
        del coords[0:2]
        del coords[2]
        latlong = []
        for coord in coords:
            latlong.append(float(coord))
        ctcoords.append(tuple(latlong))
        count += 1
    line = ctgpx.readline()
ctgpx.close()
ct = LineString(ctcoords)
x,y = ct.xy

plt.plot(y,x, color = 'darkblue')

# Reading and creating line from Collegiate West gpx file

cwgpx = open('collegiatewest.txt' , 'r')
line = cwgpx.readline()
cwcoords = []
count = 0
while line:
    coords = line.split("\t")
    if(len(coords) == 7):
        del coords[0:2]
        del coords[2:6]
        latlong = []
        for coord in coords:
            latlong.append(float(coord))
        cwcoords.append(tuple(latlong))
        count += 1
    line = cwgpx.readline()
cwgpx.close()
cw = LineString(cwcoords)
x,y = cw.xy
plt.plot(y,x, color = 'blue')

# Create mile markers for each point in CT, dictionary[coordinate pair] = mile marker

milemarkers = {}
distance = 0
for i in range(1,len(ctcoords)):
    d = getdistance(ctcoords[i-1][0],ctcoords[i-1][1],ctcoords[i][0],ctcoords[i][1])
    milemarkers[ctcoords[i]] = distance + d
    distance += d

# Create mile markers for each point of Collegiate West

cwmilemarkers = {}
distance = 0
for i in range(1,len(cwcoords)):
    d = getdistance(cwcoords[i-1][0],cwcoords[i-1][1],cwcoords[i][0],cwcoords[i][1])
    cwmilemarkers[cwcoords[i]] = distance + d
    distance += d

# Initialize text to be sent as SMS

text = ""

# Accessing fire boundary data from Wildland Fire Interagency Geospatial Services API

api_url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Perimeters/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
response = requests.get(api_url)
all = response.json()
fires = all['features']

# Accessing CO county geometry data

# api_url = "https://www.cohealthmaps.dphe.state.co.us/arcgis/rest/services/OPEN_DATA/cdphe_geographic_analysis_boundaries/MapServer/5/query?where=1%3D1&outFields=*&outSR=4326&f=json"
# response = requests.get(api_url)
# all = response.json()
# counties = all['features']
# #county name = counties[i]['attributes']['LABEL']
# #county coords = counties[i]['geometry']['rings'][0]

# Accessing historical wildfire data over 100,000 acres (to test tool with large fires that may cross trail)

# api_url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Historic_Geomac_Perimeters_Combined_2000_2018/FeatureServer/0/query?where=state%20%3D%20%27CO%27&outFields=*&outSR=4326&f=json"
# response = requests.get(api_url)
# all = response.json()
# histfires = all['features']

# Check if fires are in CO, add fire info (name)

cofires = []
cofireshapes = []
for fire in fires:
    inco = False
    listofcoords = []
    for key in fire:
        coords = fire['geometry']['rings']
        for coordlist in coords:
            for coord in coordlist:
                if(coord[1] > 37 and coord[1] < 41 and coord[0] > -109.05 and coord[0] < -102.05):
                    listofcoords.append(coord)
                    inco = True
    if(inco == True):
        cofires.append(fire)
        cofireshapes.append(listofcoords)

# Creating test fire to check trail crossing function

# listofcoords = [(-107.5,37.6), (-107.5, 37.9), (-107.8, 37.9), (-107.8,37.6)]
# cofireshapes.append(listofcoords)
# testfire = {'attributes': {'irwin_IncidentName': 'Test', 'poly_GISAcres': 666}}
# testfire['attributes']['irwin_IncidentName'] = 'Test'
# testfire['attributes']['poly_GISAcres'] = 666
# cofires.append(testfire)

# Add number of fires to text

text += "Total CO Fires: "
text += str(len(cofires))
text += "\n"

# Add fire names and areas to text

for fire in cofires:
    text += str(fire['attributes']['irwin_IncidentName'])
    text += ' Fire - '
    if fire['attributes']['poly_GISAcres'] is not None:
        text += str(round(fire['attributes']['poly_GISAcres']))
    else:
        text += "N.A."
    text += " acres, contaiment: "
    if fire['attributes']['irwin_PercentContained'] is not None:
        text += str(round(fire['attributes']['irwin_PercentContained']))
        text += "%\n"
    else:
        text += "N.A.\n"

# Make fires list which contains shapely shapes of each fire

for shape in cofireshapes:
    poly = Polygon(shape)
    x,y = poly.exterior.xy
    plt.plot(x,y, color = "crimson")

# Check if any fires cross the trail

ctlist = list(ct.coords)
for i in range(len(ctlist)):
    item = list(ctlist[i])
    temp = item[0]
    item[0] = item[1]
    item[1] = temp
    ctlist[i] = tuple(item)

ctline = LineString(ctlist)
cross = False
ncross = 0
for i in range(len(cofireshapes)):
    if(ctline.intersects(Polygon(cofireshapes[i]))):
        cross = True
        ncross += 1
        crossline = ctline.intersection(Polygon(cofireshapes[i]))
        x,y = crossline.xy
        plt.plot(x,y, color = 'yellow')
        crosslist = list(crossline.coords)
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
    #print("The ", cofires[i]['attributes']['irwin_IncidentName'], " Fire is: ", closestpoints[i][0], "mi. from the Colorado trail at mile marker:", round(milemarkers[closestpoints[i][2]],1))

# Send SMS update with Twilio

# account_sid = "ACf8c276acb53197b719e5b9e07d89991d"
# auth_token  = "8be95e1fd81a365058c4e084b86c00c0"

# client = Client(account_sid, auth_token)

print("number of characters:", len(text))
print(text)
#print(message.sid)

# Save visuals

plt.savefig("fire.png", dpi = 200)



#app = Flask(__name__)
@app.route("/sms", methods=['POST'])

def sms_reply():
    number = request.form['From']
    message_body = request.form['Body']
    # Do stuff to get response_String
    response = text
    resp = MessagingResponse()
    resp.message(response)
    return str(resp)

if __name__ == "__main__":
    app.run(host = LISTEN_ADDRESS, port = LISTEN_PORT)


# TODO:
# add evacuation orders for counties crossed by CT (check if any resupply towns are in other counties)
# ADD PERCENT CONTAINMENT
# 