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

### Recent Improvements
- The latest iteration of this application support more trails, including:
  - Colorado Trail (CT)
  - Pacific Crest Trail (PCT)
  - Arizona Trail (AZT)
  - Pacific Northwest Trail (PNT)
  - Continental Divide Trail (CDT)

![CDT_fires](https://user-images.githubusercontent.com/99096893/222990819-ecde378d-f1f4-454f-9ea9-dde2bc7c5789.png)
This image shows all supported trails, their 50 mile fire detection buffer zone, and some sample test fires to assess refactoring changes made to the app.

- Unit testing was implemented to test both the new FireTracker class methods, as well as the Flask application that users interact with directly through SMS

Example Colorado Trail test output with the test fires from above:

        CT test_sms PASSED: sms created
        
        Total fires within 50 miles of the CT: 2
        Test Fire 1 Fire (Colorado, 02/22/23) - 50 acres, 95% contained
        Test Fire 2 Fire (Colorado and New Mexico, 02/22/23) - 50 acres, 95% contained
        The Test Fire 1 Fire is 2 mi. from the CT at mile marker 9
        1 fire(s) currently cross the CT
        The Test Fire 2 Fire crosses the CT at mi. 365 to mi. 493

