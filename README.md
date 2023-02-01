# SMS Wildfire Alert System for Thru-Hikers

This project was inspired by a close call with a wildfire while hiking the PCT in 2021. It requests fire location data from the National Interagency Fire Center and plots it against gps data of a hiking trail (in this case the Colorado Trail but with potential adaptations for other National Scenic Trails).
<br/><br/>
Data can be received as an SMS message either with a cell phone or off-grid satellite communication device, so that even when a hiker is not being reached by a SMS emergency alert because they are out of service, they can still request an update through this app. 
<br/><br/>
The app does not request specific location data from the user, but gives an update for the whole trail, from which the user can assess relevant information based on their location. Future implementations for longer trails may request a mile marker in the message body and use that to tailor location-specific updates, such as any active fires within 100 trail miles.
<br/><br/>

<img src='https://i.imgur.com/dk1ppe5.png' alt='image showing the colorado trail with 2 nearby fires'/>
<br/>
![image showing sms update](https://i.imgur.com/acwUpbV.jpg)
<br/>
![image showing sms update](https://i.imgur.com/OcPFsgf.jpg)

