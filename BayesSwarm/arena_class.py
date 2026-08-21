import numpy as np

class Arena:
    """
        Defines the arena configuration for initializing simulation:
            - Arena bounds
            - Arena obstacles
    """
        
    def __init__(self):
        self.ARENA_LOWER_BOUND = np.array([0,0])
        self.ARENA_UPPER_BOUND = np.array([2.4, 2.4])




