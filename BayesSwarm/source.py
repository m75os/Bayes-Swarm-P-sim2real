#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Payam Ghassemi | 02/19/2020 """

import numpy as np

class Source:
    def __init__(self, id):

        self.id = id
        self.source_dim = 2
        if self.id == 0:
            self.source_0_init()
        elif self.id == 1:
            self.source_1_init()
        elif self.id == 2:
            self.source_2_init()
        elif self.id == 3:
            self.source_3_init()
        elif self.id == 4:
            self.source_4_init()
        elif self.id == 5:
            self.source_5_init()
        elif self.id == 51:
            self.source_51_init()
        elif self.id == 6:
            self.source_6_init()
        elif self.id == 7:
            self.source_7_init()
        elif self.id == 8:
            self.source_8_init()
        elif self.id == 9:
            self.source_9_init()
        elif self.id == 10:
            self.source_10_init()
        else:
            self.source_1_init()
        
    def get_source_location(self):
        
        return self.source_location

    def measure(self, location):
        if self.id == 0:
            signal_value = self.source_0_measure(location)
        elif self.id == 1:
            signal_value = self.source_1_measure(location)
        elif self.id == 2:
            signal_value = self.source_2_measure(location)
        elif self.id == 3:
            signal_value = self.source_3_measure(location)
        elif self.id == 4:
            signal_value = self.source_4_measure(location)
        elif self.id == 5:
            signal_value = self.source_5_measure(location)
        elif self.id == 51:
            signal_value = self.source_5_measure(location)
        elif self.id == 6:
            signal_value = self.source_6_measure(location)
        elif self.id == 7:
            signal_value = self.source_7_measure(location)
        elif self.id == 8:
            signal_value = self.source_8_measure(location)
        elif self.id == 9:
            signal_value = self.source_9_measure(location)
        elif self.id == 10:
            signal_value = self.source_10_measure(location)
        else:
            signal_value = self.source_1_measure(location)
        
        return signal_value

    def gradient(self, location):
        if self.id == 7:
            gradient_value = self.source_7_gradient(location)
        
        return gradient_value

    def source_0_init(self): # Based on 99 in my Matlab code
        self.source_location = np.array([.5, 0.7])
        self.time_max = 100
        self.angular_range = np.array([0,np.pi/2])
        self.arena_lb = np.array([0,0])
        self.arena_ub = np.array([2.4, 2.4])
        self.source_detection_range = 0.05
        self.velocity = 0.1 # [m/s]
        self.decision_horizon_init = 2
        self.decision_horizon = 10
        self.local_penalizing_coef = {"M": 1.2, "L": 50}
        self.communication_range = 2
    
    def source_0_measure(self, location):
        c = self.source_location
        x = location
        sig1 = -3.0
        
        dx1 = x - c
        if np.size(location) > self.source_dim:
            dx11 = np.linalg.norm(dx1, axis=1)**2
        else:
            dx11 = np.dot(dx1,dx1)
        
        f = np.exp(dx11/sig1)

        return f

    def source_7_init(self): # Based on Case 1 in MRS paper, but adopted for IROS2020
        self.source_location = np.array([1., 2.])
        self.time_max = 100
        self.angular_range = np.array([0,np.pi/2])
        self.arena_lb = np.array([0,0])
        self.arena_ub = np.array([2.4, 2.4])
        self.source_detection_range = 0.05
        self.velocity = 0.1 # [m/s]
        self.decision_horizon_init = 10
        self.decision_horizon = 10
        self.local_penalizing_coef = {"M": 1.2, "L": 2} #100
        self.communication_range = 0.5
    
    def source_7_measure(self, location):
        c = self.source_location
        x = location
        sig1 = -3.0
        sig2 = -0.5
        
        dx1 = x - c
        dx2 = x - np.array([2., .5])
        if np.size(location) > self.source_dim:
            dx11 = np.linalg.norm(dx1, axis=1)**2
            dx22 = np.linalg.norm(dx2, axis=1)**2
        else:
            dx11 = np.dot(dx1,dx1)
            dx22 = np.dot(dx2,dx2)

        f = np.exp(dx11/sig1) + 0.5 * np.exp(dx22/sig2)

        return f
    
    def source_7_gradient(self, location):
        c = self.source_location
        x = location
        sig1 = -3.0
        sig2 = -0.5
        ## exp(a(x+b)^2+c) --d/dx--> 2a(x+b)exp(a(x+b)^2+c)
        dx1 = x - c
        dx2 = x - np.array([2., .5])
        if np.size(location) > self.source_dim:
            dx11 = np.linalg.norm(dx1, axis=1)**2
            dx22 = np.linalg.norm(dx2, axis=1)**2
        else:
            dx11 = np.dot(dx1,dx1)
            dx22 = np.dot(dx2,dx2)

        dfx = []
        for i in range(2):
            dfx.append(2*(1/sig1)*(x[i]+dx1[i])*np.exp(dx11/sig1) + 2*(1/sig2)*(x[i]+dx2[i])*0.5*np.exp(dx22/sig2))

        return np.linalg.norm(dfx)

    def get_source_info(self):
        
        return self.velocity, self.decision_horizon, self.source_detection_range, self.source_location,\
                self.angular_range, self.time_max, self.arena_lb, self.arena_ub
    
    def get_source_info_arena(self):
        
        return self.angular_range, self.arena_lb, self.arena_ub
    
    def get_source_info_robot(self):
        
        return self.velocity, self.decision_horizon, self.decision_horizon_init, self.source_detection_range

    def get_source_info_mission(self):
        
        return self.source_location, self.time_max

    def get_source_bayes_settings(self):
        
        return self.local_penalizing_coef

    def set_velocity(self, velocity):
        Warning('Default velocity changed from {} to {}'.format(self.velocity, velocity))
        self.velocity = velocity
    
    def set_decision_horizon(self, decision_horizon):
        Warning('Default decision-horizon changed from {} to {}'.format(self.decision_horizon, decision_horizon))
        self.decision_horizon = decision_horizon
    
    def get_source_communication_range(self):
        return self.communication_range

    def get_data_for_plot(self):
        N = 100
        x1 = np.linspace(self.arena_lb[0], self.arena_ub[0], N)
        x2 = np.linspace(self.arena_lb[1], self.arena_ub[1], N)
        X1, X2 = np.meshgrid(x1,x2)
        X = np.hstack((X1.reshape(-1,1), X2.reshape(-1,1)))
        Y = self.measure(X)
        Y = Y.reshape(N,-1)

        return X1, X2, Y

