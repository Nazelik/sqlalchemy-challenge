# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")


# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)


# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station


# Create our session (link) from Python to the DB
##session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)



#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"<h1>Climate Analysis Data of Honolulu, Hawaii for Trip Planning</h1><br>"
        f"<h2>Available Routes:</h2><br>"

        f"1. One year (2016-08-23 -- 2017-08-23) precipitation data:<br>"
        f"<a href='http://127.0.0.1:5000/api/v1.0/precipitation'>/api/v1.0/precipitation<a/><br><br>"

        f"2. List of stations:<br>"
        f"<a href='http://127.0.0.1:5000/api/v1.0/stations'>/api/v1.0/stations<a/><br><br>"

        f"3. One year (2016-08-23 -- 2017-08-23) temperature data for the most active station:<br/>"
        f"<a href='http://127.0.0.1:5000/api/v1.0/tobs'>/api/v1.0/tobs<a/><br><br>"

        f"4. To get the minimum, avarage and maximum temperatures for a <b>specific date</b> of your choice,\
            append  the following to the current URL:"
        f"<h4> /api/v1.0/yyyy-mm-dd </h4>" 
        f"where 2010/01/01 <= yyyy-mm-dd <= 2017-08-23.<br><br>"

        f"5. To get the minimum, avarage and maximum temperatures for a <b>specific date range</b> of your choice,\
            append  the following to the current URL:"
        f"<h4> /api/v1.0/yyyy-mm-dd/yyyy-mm-dd </h4>" 
        f"where first date < second date and 2010/01/01 <= yyyy-mm-dd <= 2017-08-23."
    )

# 2. Convert the query results from your precipitation analysis 
# (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.
# Return the JSON representation of your dictionary.

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Find the most recent date in the data set.
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    # Calculate the date one year from the last date in data set.
    year_ago_date = dt.date(2017,8,23) - dt.timedelta(days=365)

    # Perform a query to retrieve the data and precipitation scores
    recent_year_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= year_ago_date).all()


    session.close()

    # Convert list of tuples into dictionary
    date_prcp_dict = {}
    for el in recent_year_data:
        date = el[0]
        prcp = el[1]
        date_prcp_dict[date] = prcp


    return jsonify(date_prcp_dict)


# 3. Return a JSON list of stations from the dataset.

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    stations = session.query(Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()

    session.close()

    stations_list = []
    for el in stations:
        station = el[0]
        name = el[1]
        latitude = el[2]
        longitude = el[3]
        elevation = el[4]
        stations_list.append({"station":station, "name":name, "latitude":latitude, "longitude":longitude, "elevation":elevation})




    return jsonify(stations_list)

# 4. Query the dates and temperature observations of the most-active station for the previous year of data.
#    Return a JSON list of temperature observations for the previous year.

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    year_ago_date = dt.date(2017,8,23) - dt.timedelta(days=365)

    station_count = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()

    for row in station_count:
        print(row)

    active_st = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()
    most_active = active_st[0]


    one_year_temp_active_st = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station==most_active).\
                            filter(Measurement.date >= year_ago_date).all()
    one_year_temp_df = pd.DataFrame(one_year_temp_active_st, columns = ['date', 'tobs'])
    one_year_temp_df.set_index('date', inplace = True) 

    session.close()

    tobs_list = []
    for el in one_year_temp_active_st:
        tob_dict = {}
        date = el[0]
        tob = el[1]
        tob_dict[date] = tob
        tobs_list.append(tob_dict)

    return jsonify(tobs_list)


# 5. Return a JSON list of the minimum temperature, the average temperature, 
#    and the maximum temperature for a specified start or start-end range.
#    For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
#    Accepts the start date as a parameter from the URL 
#    Returns the min, max, and average temperatures calculated from the given start date to the end of the dataset 
@app.route("/api/v1.0/<start>")
def start(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    extreme_avg_temps = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
                        filter(Measurement.date >= start).all()
    TMIN = extreme_avg_temps[0][0]

    TAVG = extreme_avg_temps[0][1]
    TMAX = extreme_avg_temps[0][2]                  
    session.close()

    temp_list = []
    temp_dict = {}
    temp_dict["min_temp"] = TMIN
    temp_dict["avg_temp"] = TAVG
    temp_dict["max_temp"] = TMAX
    temp_list.append(temp_dict)

    return jsonify(temp_list)


# 6. Return a JSON list of the minimum temperature, the average temperature, 
#    and the maximum temperature for a specified start or start-end range.
#    For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, 
#    inclusive.  
#    Accepts the start and end dates as parameters from the URL.
#    Returns the min, max, and average temperatures calculated from the given start date to the given end date.


@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    extreme_avg_temps = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
                        filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    TMIN = extreme_avg_temps[0][0]

    TAVG = extreme_avg_temps[0][1]
    TMAX = extreme_avg_temps[0][2]                  
    session.close()

    temp_list = []
    temp_dict = {}
    temp_dict["min_temp"] = TMIN
    temp_dict["avg_temp"] = TAVG
    temp_dict["max_temp"] = TMAX
    temp_list.append(temp_dict)

    return jsonify(temp_list)




if __name__ == '__main__':
    app.run(debug=True)
