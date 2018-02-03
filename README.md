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

## Details

All the survey parameters are defined in one json object.  Here is the example input:

Example input:
```javascript
{
        "MinEl": 5,
        "MeridianBuffer": 4,
        "PoleBuffer": 20,
        "Fov": 10,
        "Lat": 40,
        "Lon": -84,
        "Exposure": 1,
        "Area": 5
}
```

All angle units are in degrees... that's the only note I can think of here.

### Survey Grid

The survey is constructed using elevation masks, keep out zones around the local meridian and the celestial pole.  Grid density is determined by the "Area" parameter (deg<sup>2</sup>) which represents the average area assigned to each grid point (see references).  The larger the area, the fewer the survey points.  This produces a regular distribution of points in spherical space (no increase in grid density near zenith).

![alt text](https://github.com/dam90/tpoint/blob/master/docs/images/survey_2D.png "2D Survey Grid")

![alt text](https://github.com/dam90/tpoint/blob/master/docs/images/survey_3D.png "3D Survey Grid")

### Survey Sequence

Once the survey grid is constructed, it's split into two sets along local meridian.  A survey sequence is developped using a solution to the "Travelling Salesman Problem" (TSP) for each half, and then they are rejoined.  The goal is to find "one of the fastest" routes through all the grid points, with only only one meridian flip.

![alt text](https://github.com/dam90/tpoint/blob/master/docs/images/tsp_2D.png "2D Path Plot")

![alt text](https://github.com/dam90/tpoint/blob/master/docs/images/tsp_3D.png "3D Path Plot")
