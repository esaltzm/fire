# SMS Wildfire Alert System for Thru-Hikers

This project was inspired by a close call with a wildfire while hiking the PCT in 2021. It requests fire location data from the National Interagency Fire Center and plots it against gps data of a user-specified National Scenic Trail.
<br/><br/>
Data can be received as an SMS message either with a cell phone or off-grid satellite communication device, so that even when a hiker is out of service, without internet access or unreachable by location-based emergency alerts, they can still request an update through this interface. 
<br/><br/>
The app does not request specific location data from the user, just the trail they are requesting information for. It provides update for the whole trail, from which the user can assess relevant information based on their location. Future implementations for longer trails may request a mile marker in the message body and use that to tailor location-specific updates, such as any active fires within 100 trail miles.
<br/><br/>

![image showing ct with 2 fires](https://i.imgur.com/76a82iF.jpg)
<br/>
<div style='display: flex; gap: 30px;'>
  <img src='https://i.imgur.com/acwUpbV.jpg' alt='image showing sms update' style='width: 400px'/>
  <img src='https://i.imgur.com/OcPFsgf.jpg' alt='image showing sms update' style='width: 400px'/>
</div>

Unit testing was implemented to assess the interface using model fire perimeters for different trails:

![AZT_fires](https://user-images.githubusercontent.com/99096893/221447111-9dea5890-5cdc-480a-94b7-0c86203536b0.png)
<img width="844" alt="arizona test fires" src="https://user-images.githubusercontent.com/99096893/221447168-dfe9cb99-5742-436c-897b-b55af893a641.png">
![CT_fires](https://user-images.githubusercontent.com/99096893/221447126-83f77a7f-3815-4585-8f3c-6871624d0223.png)
<img width="844" alt="colorado test fires" src="https://user-images.githubusercontent.com/99096893/221447137-902b7971-10c8-40dd-a2b2-e168dc2acef9.png">
