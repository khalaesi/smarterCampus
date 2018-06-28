# Read data from all sensors and print
# Includes: BME680, TSL2561 Light Sensor, USB microphone test


import sqlite3
import bme680
from tsl2561 import TSL2561
import time
import os
import numpy
import pyaudio
import analyse
import requests
import argparse

# Some variables
REPEAT = 5
WAIT_PERIOD = 2
URL = 'https://corlysis.com:8086/write'
READING_DATA_PERIOD_MS = 5000.0
SENDING_PERIOD = 2
MAX_LINES_HISTORY = 1000

def main():
    count = 0
    bme = bme680.BME680(i2c_addr=0x77)

    # Initialize db
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="data")
    parser.add_argument("token", help="35d4aa441b94cdbae7404050edd3fad6")
    args = parser.parse_args()
    corlysis_params = {"db": args.db, "u": "token", "p": args.token, "precision": "ms"}

    #Initialize sensor
    bme.set_humidity_oversample(bme680.OS_2X)
    bme.set_pressure_oversample(bme680.OS_4X)
    bme.set_temperature_oversample(bme680.OS_8X)
    bme.set_filter(bme680.FILTER_SIZE_3)
    bme.set_gas_status(bme680.ENABLE_GAS_MEAS)
    
    # Initialize USB mic
    #pyaud = pyaudio.PyAudio()
    #stream = pyaud.open(
	#format = pyaudio.paInt16,
	#channels = 1,
	#rate = 32000,
	#input_device_index = 2,
	#input = True)

    payload = ""
    counter = 1
    problem_counter = 0

    # Main loop
    while (True):
	    unix_time_ms = int(time.time()*1000)
		
	    # Read from BME
	    bme.get_sensor_data()
	    tempCelcius = float("{0:.2f}".format(bme.data.temperature))
	    #Convert the above variable to fahrenheit
	    temperature = float(tempCelcius*(9/5) + 32)
	    pressure = float("{0:.2f}".format(bme.data.pressure))
	    humidity = float("{0:.2f}".format(bme.data.humidity))
	    gas = float("{0:.2f}".format(bme.data.gas_resistance))
			
	    # Read from lux sensor
	    tsl = TSL2561(debug=True)
	    luxVal = tsl.lux()
	    
	    # Read from USB mic
            #rawsamps = stream.read(2048, exception_on_overflow=False)
            #samps = numpy.fromstring(rawsamps, dtype=numpy.int16)
            #dB = analyse.loudness(samps) + 60
	
	    line = "sensors_data temperature={},pressure={},humidity={},luxVal={} {}\n".format(temperature,
             pressure,
             humidity,
             luxVal,
             unix_time_ms)
            payload += line
		
	    if counter % SENDING_PERIOD == 0:
            	try:
                	# try to send data to cloud
                	r = requests.post(URL, params=corlysis_params, data=payload)
                	if r.status_code != 204:
                    		raise Exception("data not written")
                	payload = ""
            	except:
                	problem_counter += 1
                	print('cannot write to InfluxDB')
                	if problem_counter == MAX_LINES_HISTORY:
                    		problem_counter = 0
                    		payload = ""

            counter += 1
		
	    print("      BME680")
	    print("Temperature: {}".format(temperature))
	    print("Pressure: {}".format(pressure))
	    print("Humidity: {}".format(humidity))
	    print("Gas: {}".format(gas))
	    print('\n')
	    print("     TSL2561")
            print("Lux: {}".format(luxVal))
            print('\n')
            print("     USB Mic")
            print ("------------------------")
            #print ("Sound in dB: {}".format(dB)) 
            
			
	    time_diff_ms = int(time.time()*1000) - unix_time_ms
            print(time_diff_ms)
            if time_diff_ms < READING_DATA_PERIOD_MS:
            	time.sleep((READING_DATA_PERIOD_MS - time_diff_ms)/1000.0)

    con.commit()
    con.close()
# Run main
if __name__ == '__main__':
    main()

