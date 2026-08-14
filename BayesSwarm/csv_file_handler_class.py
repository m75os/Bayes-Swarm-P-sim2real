import csv
import os
import pathlib

import time # Temporary, delete later

from datetime import datetime 
from zoneinfo import ZoneInfo

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

        #print(f"min_x = {self.min_x}")
        #print(f"min_y = {self.min_y}")
        #print(f"max_x = {self.max_x}")
        #print(f"max_y = {self.max_y}")
 
    def retrieve_rssi(self, x_coord, y_coord):
        """ 
            Retrieves rssi value from files in csv_data 
            Data in form [waypoint_num, x, y, rssi_strength]
 
            Want to collect 5 data points for signal estimation

            csv source data starts at row 3
        """
    
        no_left_x_coord = False
        no_right_x_coord = False
        no_top_y_coord = False
        no_bottom_y_coord = False

        matching_coordinate_found = False
        coord_difference_tolerance = 0.05

        x_coord_left = 0
        x_coord_right = 0
        y_coord_above = 0
        y_coord_below = 0

        found_x_coord_left = False
        found_x_coord_right = False
        found_y_coord_above = False
        found_y_coord_below = False

        coord_neighbor_tolerance = 0.05

        # Determines whether the entered coordinate is near the source boundaries
        edge_boundary_tolerance = 0.1 

        distance_to_left_edge = abs(x_coord - self.min_x)
        distance_to_right_edge = abs(x_coord - self.max_x)
        distance_to_top_edge = abs(y_coord - self.max_y)
        distance_to_bottom_edge = abs(y_coord - self.min_y)

        if (distance_to_left_edge < edge_boundary_tolerance):
            no_left_x_coord = True
            print("At left edge, not sampling left coordinate")
        elif (distance_to_right_edge < edge_boundary_tolerance):
            no_right_x_coord = True
            print("At right edge, not sampling right coordinate")
        if (distance_to_top_edge < edge_boundary_tolerance):
            no_top_y_coord = True
            print("At top edge, not sampling top coordinate")
        elif (distance_to_bottom_edge < edge_boundary_tolerance):
            no_bottom_y_coord = True
            print("At top bottom edge, not sampling bottom coordinate")
       
        with open(self.CSV_DATA_SOURCE, 'r') as csv_file:
            file_data = csv.reader(csv_file)

            while not matching_coordinate_found:

                csv_file.seek(0)
                file_data = csv.reader(csv_file)
 
                for row, row_data in enumerate(file_data):

                    if (row > 3):
                        source_x_coord = float(row_data[1])
                        source_y_coord = float(row_data[2])
                        #print(f"row # = {row}")    
                        #print(f"row_data[0] = {row_data[0]}")
                        #print(f"row_data[1] = {row_data[1]}")
                        #print(f"row_data[2] = {row_data[2]}")
                        #print(f"row_data[3] = {row_data[3]}")
                        #print(f"difference_tolerance = {coord_difference_tolerance}")
    
                        x_coord_difference = abs(source_x_coord - x_coord)
                        y_coord_difference = abs(source_y_coord - y_coord)
     
                        if (x_coord_difference < coord_difference_tolerance and
                            y_coord_difference < coord_difference_tolerance):
                            
                            x_coord_center = source_x_coord 
                            y_coord_center = source_y_coord 
                            rssi_strength_center = float(row_data[3])
                        
                            #print(f"coord_difference_tolerance = {coord_difference_tolerance}")
                            print("Center coordinate: ")
                            print(f"[{x_coord_center},{y_coord_center}, {rssi_strength_center}]")
                            matching_coordinate_found = True

                coord_difference_tolerance += 0.02
            
            # Find coordinate below
            if (not no_bottom_y_coord):

                coord_neighbor_tolerance = 0.05
                coord_difference_tolerance = 0.05
                with open(self.CSV_DATA_SOURCE, 'r') as csv_file:

                    while not found_y_coord_below:
                        csv_file.seek(0)
                        file_data = csv.reader(csv_file)

                        for row, row_data in enumerate(file_data):
                            if (row > 3):
                                source_x_coord = float(row_data[1])
                                source_y_coord = float(row_data[2])
    
                                #print(f"waypoint = {row_data[0]}")
                                #print(f"source_x_coord = {row_data[1]}")
                                #print(f"source_y_coord = {row_data[2]}")
                                #print(f"row_data[3] = {row_data[3]}")
                                #print(f"coord_neighbor_tolerance = {coord_neighbor_tolerance}")
                                #print("\n")
    
                                x_coord_difference = abs(source_x_coord - x_coord_center)
                                y_coord_difference = abs(source_y_coord - y_coord_center)
    
                                if (x_coord_difference < coord_difference_tolerance):
                                    if (source_y_coord < y_coord_center and
                                        y_coord_difference < coord_neighbor_tolerance):
                                       
                                        x_coord_below = source_x_coord 
                                        y_coord_below = source_y_coord
                                        rssi_strength_below = float(row_data[3])
                                        print("Coordinate below: ")
                                        print(f"[{x_coord_below}, {y_coord_below}, {rssi_strength_below}]")
                                        found_y_coord_below = True
    
                        coord_neighbor_tolerance += 0.02
                        
                        # If no y value can be found, then change the x value
                        if (coord_neighbor_tolerance > 0.2):
                            coord_neighbor_tolerance = 0.05
                            coord_difference_tolerance = 0.05


            # Find coordinate above
            if (not no_top_y_coord):

                coord_neighbor_tolerance = 0.05
                coord_difference_tolerance = 0.05
                with open(self.CSV_DATA_SOURCE, 'r') as csv_file:

                    while not found_y_coord_above:
                        csv_file.seek(0)
                        file_data = csv.reader(csv_file)

                        for row, row_data in enumerate(file_data):
                            if (row > 3):
                                source_x_coord = float(row_data[1])
                                source_y_coord = float(row_data[2])
    
                                #print(f"waypoint = {row_data[0]}")
                                #print(f"source_x_coord = {row_data[1]}")
                                #print(f"source_y_coord = {row_data[2]}")
                                #print(f"row_data[3] = {row_data[3]}")
                                #print(f"coord_neighbor_tolerance = {coord_neighbor_tolerance}")
                                #print("\n")
    
                                x_coord_difference = abs(source_x_coord - x_coord_center)
                                y_coord_difference = abs(source_y_coord - y_coord_center)
    
                                if (x_coord_difference < coord_difference_tolerance):
                                    if (source_y_coord > y_coord_center and
                                        y_coord_difference < coord_neighbor_tolerance):
                                       
                                        x_coord_above = source_x_coord 
                                        y_coord_above = source_y_coord
                                        rssi_strength_above = float(row_data[3])
                                        print("Coordinate above: ")
                                        print(f"[{x_coord_above}, {y_coord_above}, {rssi_strength_above}]")
                                        found_y_coord_above = True
    
                        coord_neighbor_tolerance += 0.02

                        # If no y value can be found, then change the x value
                        if (coord_neighbor_tolerance > 0.2):
                            coord_neighbor_tolerance = 0.05
                            coord_difference_tolerance = 0.05



            # Find coordinate to the left
            if (not no_left_x_coord):

                coord_neighbor_tolerance = 0.05
                coord_difference_tolerance = 0.05
                with open(self.CSV_DATA_SOURCE, 'r') as csv_file:

                    while not found_x_coord_left:
                        csv_file.seek(0)
                        file_data = csv.reader(csv_file)

                        for row, row_data in enumerate(file_data):
                            if (row > 3):
                                source_x_coord = float(row_data[1])
                                source_y_coord = float(row_data[2])
    
                                #print(f"waypoint = {row_data[0]}")
                                #print(f"source_x_coord = {row_data[1]}")
                                #print(f"source_y_coord = {row_data[2]}")
                                #print(f"row_data[3] = {row_data[3]}")
                                #print(f"coord_neighbor_tolerance = {coord_neighbor_tolerance}")
                                #print("\n")
    
                                x_coord_difference = abs(source_x_coord - x_coord_center)
                                y_coord_difference = abs(source_y_coord - y_coord_center)
    
                                if (y_coord_difference < coord_difference_tolerance):
                                    if (source_x_coord < x_coord_center and
                                        x_coord_difference < coord_neighbor_tolerance):
                                        
                                        x_coord_left = source_x_coord
                                        y_coord_left = source_y_coord
                                        rssi_strength_left  = float(row_data[3])
                                        print("Coordinate left: ")
                                        print(f"[{x_coord_left}, {source_y_coord}, {rssi_strength_left}]")
                                        found_x_coord_left = True
    
                        coord_neighbor_tolerance += 0.02

                        # If no x value can be found, then change the y value
                        if (coord_neighbor_tolerance > 0.2):
                            coord_neighbor_tolerance = 0.05
                            coord_difference_tolerance = 0.05



            # Find coordinate to the right
            if (not no_right_x_coord):

                coord_neighbor_tolerance = 0.05
                coord_difference_tolerance = 0.05
                with open(self.CSV_DATA_SOURCE, 'r') as csv_file:

                    while not found_x_coord_right:
                        csv_file.seek(0)
                        file_data = csv.reader(csv_file)

                        for row, row_data in enumerate(file_data):
                            if (row > 3):
                                source_x_coord = float(row_data[1])
                                source_y_coord = float(row_data[2])
    
                                #print(f"waypoint = {row_data[0]}")
                                #print(f"source_x_coord = {row_data[1]}")
                                #print(f"source_y_coord = {row_data[2]}")
                                #print(f"row_data[3] = {row_data[3]}")
                                #print(f"coord_neighbor_tolerance = {coord_neighbor_tolerance}")
                                #print("\n")
    
                                x_coord_difference = abs(source_x_coord - x_coord_center)
                                y_coord_difference = abs(source_y_coord - y_coord_center)
    
                                if (y_coord_difference < coord_difference_tolerance):
                                    if (source_x_coord > x_coord_center and
                                        x_coord_difference < coord_neighbor_tolerance):
                                        
                                        x_coord_right = source_x_coord
                                        y_coord_right = source_y_coord
                                        rssi_strength_right = float(row_data[3])
                                        print("Coordinate right: ")
                                        print(f"[{x_coord_right}, {source_y_coord}, {rssi_strength_right}]")
                                        found_x_coord_right = True
    
                        coord_neighbor_tolerance += 0.02

                        # If no x value can be found, then change the y value
                        if (coord_neighbor_tolerance > 0.2):
                            coord_neighbor_tolerance = 0.05
                            coord_difference_tolerance = 0.05

        return [x_coord_center, y_coord_center, rssi_strength_center,
                x_coord_above, y_coord_above, rssi_strength_above,
                x_coord_below, y_coord_below, rssi_strength_below,
                x_coord_left, y_coord_left, rssi_strength_left,
                x_coord_right, y_coord_right, rssi_strength_right]

          
csv_file_inst = csvFileHandler()

csv_file_inst.choose_csv_source()
csv_file_inst.get_csv_arena_bounds()
[x_coord_center, y_coord_center, rssi_strength_center, \
                x_coord_above, y_coord_above, rssi_strength_above, \
                x_coord_below, y_coord_below, rssi_strength_below, \
                x_coord_left, y_coord_left, rssi_strength_left, \
                x_coord_right, y_coord_right, rssi_strength_right] = csv_file_inst.retrieve_rssi(1, 1)

#print(f"x_coor = {x_coor}")
#print(f"y_coor = {y_coor}")
#print(f"rssi_strength = {rssi_strength}")
