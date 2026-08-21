# /usr/bin/env python
# -*- coding: utf-8 -*-
""" Payam Ghassemi | 02/19/2020 """

import numpy as np
from BayesSwarm.csv_file_handler import csvFileHandler

class Source:
    def __init__(self):

        # get source from csv_file for actual source
        self.csv_file_handler = csv_file_handler # From csvFileHandler() class
        self.SOURCE_LOCATION = np.array([1., 2.])
        self.SOURCE_DETECTION_RANGE = 0.05
        self.LOCAL_PENALIZING_COEF  = {"M": 1.2, "L": 2} #100
    
    def generate_artificial_signal(self): 

        num_points = 100
        x1 = np.linspace(self.arena_lb[0], self.arena_ub[0], num_points)
        x2 = np.linspace(self.arena_lb[1], self.arena_ub[1], num_points)
        X1, X2 = np.meshgrid(x1,x2)
        X = np.hstack((X1.reshape(-1,1), X2.reshape(-1,1)))
        Y = self.measure(X)
        Y = Y.reshape(num_points,-1)

        return X1, X2, Y

