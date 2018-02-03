# tpoint.py : Automated Telescope Alignment

I wanted to automatically generate tpoint alignment files for use with TheSkyX.  I need to do something like this:

1. Generate a set of survey points
2. For each survey point:
	* Slew to the survey point
	* Integrate
	* Save frame to disk with relevant metadata in FITS header
3. For each FITS file:
	* plate solve
	* store solution (if any) in FITS header
4. Compile tpoint file from aggregate FITS header data 

Survey Example

![alt text](https://github.com/dam90/tpoint/blob/master/docs/images/survey_2D.png "2D Survey Plot")

![alt text](https://github.com/dam90/tpoint/blob/master/docs/images/survey_3D.png "2D Survey Plot")

Routing Example

![alt text](https://github.com/dam90/tpoint/blob/master/docs/images/tsp_2D.png "2D Path Plot")

![alt text](https://github.com/dam90/tpoint/blob/master/docs/images/tsp_3D.png "2D Path Plot")
