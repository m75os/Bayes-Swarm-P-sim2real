import csv
import os
import pathlib
import numpy as np
import matplotlib.pyplot as plt

import time # Temporary, delete later

from datetime import datetime 
from zoneinfo import ZoneInfo
from scipy.interpolate import RBFInterpolator

class csvFileHandler:
    """ 
        Manages csv file reading and writing
        csv files used to store (x, y, RSSI_value) data points
    """

    def __init__(self):
        
        self.CURRENT_DATE = datetime.now(ZoneInfo("America/New_York"))
        self.YEAR = self.CURRENT_DATE.year
        self.MONTH = self.CURRENT_DATE.month
        self.DAY = self.CURRENT_DATE.day
        self.HOUR = self.CURRENT_DATE.hour
        self.MINUTE = self.CURRENT_DATE.minute

        self.DIRECTORY = "./csv_data/"

        self.FILENAME = "sim_data_{self.YEAR}_{self.MONTH}_{self.DAY}-"
        self.FILENAME += "{self.HOUR}-{self.MINUTE}.csv"
        self.FULL_PATH = os.path.join(self.DIRECTORY, self.FILENAME)

        self.FILE_HEADER = ["x_coord, y_coord", "rssi_strength"]
        self.FILE_FOOTER = ["waypoint_num", "x_coord", "y_coord"]

        self.CSV_DATA_SOURCE = ''

        self.header_written = False
        self.mission_complete = False

        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0

        self.coordinate_array = []
        self.rssi_array = []

    def write_csv_header(self):
        """ Writes header for (x, y, rssi_strength) to csv file """
       
        if (not self.header_written):
            if not os.path.exists(self.DIRECTORY):
                os.makedirs(self.DIRECTORY)

        with open(self.FULL_PATH, mode='w', newline='') as csv_file:
            write_header = csv.writer(csv_file)
            write_header.writerow(self.FILE_HEADER)
            self.header_written = True

    def log_path_data(self, x_coord, y_coord, rssi_strength):
        """ Log coordinate data as robot travels """
        with open(self.FULL_PATH, mode='a', newline='') as csv_file:
            file_writer = csv.DictWriter(csv_file, fieldnames=self.FILE_HEADER)
 
            file_writer.writerow({
                                        'x_coord'           : x_coord,
                                        'y_coord'           : y_coord,
                                        'rssi_strength'     : rssi_strength,
                                     })
 
    def write_csv_footer(self, waypoint_array):
        """ 
            Writes footer for (waypoint_num, x_coord, y_coord)
            after the mission has completed
            waypoint_array = [[x1, y1], ..., [xn, yn]]
        """
 
        if self.mission_complete:
 
            with open(self.FULL_PATH, mode='a', newline='') as csv_file:
                write_footer = csv.writer(csv_file)
                write_footer.writerow(self.FILE_FOOTER)
 
            with open(self.FULL_PATH, mode='a', newline='') as csv_file:
                waypoint_writer = csv.DictWriter(csv_file, fieldnames=self.FILE_FOOTER)
        
                for i in range(len(waypoint_array)):
                    waypoint_writer.writerow({
                                                'waypoint_num' : i,
                                                'x_coord' : waypoint_array[i][0],
                                                'y_coord' : waypoint_array[i][1],
                                            })
    
    def choose_csv_source(self):
        """ 
            Choose one of the csv files from csv_data to act as the 
            signal source
        """
 
        full_path = ''
        directory_file_list = os.listdir(self.DIRECTORY)
        csv_file_list = []
        chosen_file_index = 0
        title = "\n\n\t\t\tcsv files in ./csv_data: \n"
        title += "\t\t\t---------------------------\n"    
 
        # Get all csv files within ./csv_data 
        for file in directory_file_list:
    
            full_path = os.path.join(self.DIRECTORY, file)
            file_type = pathlib.Path(file).suffix
 
            if not os.path.isdir(full_path) and not file_type != ".csv": 
                csv_file_list.append(file)
 
        print(title)
 
        for i in range(len(csv_file_list)):
 
            print(f"\t{i}: {csv_file_list[i]}")
 
        print("\n")
 
        valid_file_index = False
 
        while not valid_file_index:
            chosen_file_index = int(input("Enter number to choose file: "))
 
            if (chosen_file_index > (len(csv_file_list) - 1)):
                print("Chosen index too large\n")
                continue
 
            elif (chosen_file_index < 0):
                print("Chosen file index too small\n")
                continue
 
            else:
                valid_file_index = True
 
        file = csv_file_list[chosen_file_index]
        self.CSV_DATA_SOURCE = os.path.join(self.DIRECTORY, file)

    def get_csv_arena_bounds(self):
        """
            Gets the maximum and minimum coordinate values from the csv source file
            to ensure that retrieve_rssi() doesn't search for coordinates that don't
            exist
        """

        found_edge_coordinates = False
        
        with open(self.CSV_DATA_SOURCE, 'r') as csv_file:
            file_data = csv.reader(csv_file)

            if not found_edge_coordinates:
                for row, row_data in enumerate(file_data):

                    if (row == 3):
                        self.min_x = float(row_data[1])
                        self.min_y = float(row_data[2])
                        self.max_x = self.min_x
                        self.max_y = self.min_y

                    elif (row > 3):

                        source_x_coord = float(row_data[1])
                        source_y_coord = float(row_data[2])

                        if (source_x_coord > self.max_x): 
                            self.max_x = source_x_coord
                        if (source_y_coord  > self.max_y): 
                            self.max_y = source_y_coord
                        if (source_x_coord < self.min_x): 
                            self.min_x = source_x_coord
                        if (source_y_coord < self.min_y): 
                            self.min_y = source_y_coord 

        print(f"min_x = {self.min_x}")
        print(f"min_y = {self.min_y}")
        print(f"max_x = {self.max_x}")
        print(f"max_y = {self.max_y}")

    def get_csv_file_values(self):
        """
            Places the csv file data into a coordinate list
            and rssi value list
        """

        with open(self.CSV_DATA_SOURCE, 'r') as csv_file:
            csv_file.seek(0)
            file_data = csv.reader(csv_file)
 
            for row, row_data in enumerate(file_data):
                if (row > 3):
                    x_coord = float(row_data[1])
                    y_coord = float(row_data[2])
                    rssi_value = row_data[3]

                    self.coordinate_array.append([x_coord, y_coord])
                    self.rssi_array.append(rssi_value)


    def retrieve_rssi(self, x_coord, y_coord):
        """ 
            Retrieves rssi value from files in csv_data 
            Data in form [waypoint_num, x, y, rssi_strength]
 
            Want to collect 5 data points for signal estimation

            csv source data starts at row 3
        """

        interpolator = RBFInterpolator(self.coordinate_array, self.rssi_array)
    
        rssi_value = interpolator([[x_coord, y_coord]])
        return rssi_value[0] # Returns as array so just access first element


    def plot_csv_file_waypoints(self):
        """ Plots the waypoints from the csv data for viewing """

        temp_x_coord_array = []
        temp_y_coord_array = []

        temp_x_coord_array = [x for x, y in coordinate_array]
        temp_y_coord_array = [y for x, y in coordinate_array]

        plt.plot(temp_x_coord_array, temp_y_coord_array, marker='o', color='k', linestyle='none')
        plt.show()

#------------------------------------------------        
csv_file_inst = csvFileHandler()

csv_file_inst.choose_csv_source()
csv_file_inst.get_csv_file_values()
rssi_value = csv_file_inst.retrieve_rssi(1, 1)
    
