import csv
import os
import pathlib

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
    
            for i in range(len(file_list)):
    
                print(f"\t{i}: {file_list[i]}")
    
            print("\n")
    
            valid_file_index = False
    
            while not valid_file_index:
                chosen_file_index = int(input("Enter number to choose file: "))
    
                if (chosen_file_index > (len(file_list) - 1)):
                    print("Chosen index too large\n")
                    continue
    
                elif (chosen_file_index < 0):
                    print("Chosen file index too small\n")
                    continue
    
                else:
                    valid_file_index = True
    
            file = file_list[chosen_file_index]
            self.CSV_DATA_SOURCE = os.path.join(self.DIRECTORY, file)
            

        def retrieve_rssi(self, x_coord, y_coord):
            """ 
                Retrieves rssi value from files in csv_data 
                Data in form [waypoint_num, x, y, rssi_strength]

                Want to collect 5 data points for signal estimation
            """
           
            matching_coordate_found = False 

            with open(self.CSV_DATA_SOURCE, 'r') as csv_file:
                file_data = csv.reader(csv_file)

                while not matching_coordinate_found

                    coord_difference_tolerance = 0.1

                    for row, row_data in enumerate(file_data):
                        x_coord_difference = abs(row_data[1] - x_coord)
                        y_coord_difference = abs(row_data[2] - y_coord)

                        if (x_coord_difference < coord_difference_tolerance and
                            y_coord_difference < coord_difference_tolerance):
                            
                            x_coord_higher = row_data[1]
                            x_coord_lower = file_data[row - 1][1]
                            y_coord_higher = row_data[2]
                            y_coord_lower = file_data[row -1][2]

                            return [x_coord_higher, x_coord_lower, y_coord_higher, y_coord_lower]

                    
                    coord_difference_tolerance += 0.1 

                       #TODO: finish implementation of coordinate finder within source csv file 
             

