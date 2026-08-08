#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Payam Ghassemi | 02/27/2020 """

import numpy as np 
from BayesSwarm.simulator import Simulator
from BayesSwarm.types import SimulationConfigs

import scipy.io

def main():

    n_robots                =  1
    source_id               = 7 #TODO: Remove source_id logic
    start_locations         = None
    decision_making_mode    = "bayes-swarm" # ["bayes-swarm", "levy-walk"]
    bayes_swarm_mode        = None         # ["local-penalty-sync", "local-penalty", "extended-local-penalty", None]
    filtering_mode          = "none" #"none"
    observation_frequency   = 1
    optimizers              =[None, None]         # [None, "PSO"]
    enable_full_observation = True  # [True, False]
    is_scout_team           = False
    debug                   = False
    time_profiling_enable   = False
    simulation_configs      = SimulationConfigs()

    sim = Simulator(n_robots                = n_robots,
                    source_id               = source_id,
                    start_locations         = start_locations,
                    decision_making_mode    = decision_making_mode,
                    bayes_swarm_mode        = bayes_swarm_mode,
                    filtering_mode          = filtering_mode,
                    observation_frequency   = observation_frequency,
                    optimizers              = optimizers,
                    enable_full_observation = enable_full_observation,
                    is_scout_team           = is_scout_team,
                    debug                   = debug,
                    time_profiling_enable   = time_profiling_enable,
                    simulation_configs      = simulation_configs)

    sim.run()
    sim.get_mission_metrics()

if __name__ == "__main__":
    # execute only if run as a script
    main()
