#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Payam Ghassemi | 02/19/2020 """

import numpy as np

class Source:
    def __init__(self, id):

        self.id = id

        self.source_location    = np.array([1., 2.])
        self.time_max           = 100
        self.angular_range      = np.array([0,np.pi/2])
        self.arena_lb           = np.array([0,0])
        self.arena_ub           = np.array([2.4, 2.4])
        self.source_detection_range = 0.05
        self.velocity               = 0.1 # [m/s]
        self.decision_horizon_init  = 10
        self.decision_horizon       = 10
        self.local_penalizing_coef  = {"M": 1.2, "L": 2} #100
        self.communication_range    = 0.5
    
    def get_data_for_plot(self): # TODO: Adjust so that it reads csv file data instead

        N = 100
        x1 = np.linspace(self.arena_lb[0], self.arena_ub[0], N)
        x2 = np.linspace(self.arena_lb[1], self.arena_ub[1], N)
        X1, X2 = np.meshgrid(x1,x2)
        X = np.hstack((X1.reshape(-1,1), X2.reshape(-1,1)))
        Y = self.measure(X)
        Y = Y.reshape(N,-1)

        return X1, X2, Y

