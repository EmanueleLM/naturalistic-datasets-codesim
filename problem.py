import random 
import string 

class GoodExchange(object):
    def __init__(self, n_agents:int, n_goods:int):
        self.n_agents = n_agents
        self.n_goods = n_goods
        
        # An agent has a name (a letter from a to z) and a number of goods (from 0 to n_goods)
        self.agents = {string.ascii_lowercase[i]: n_goods for i in range(self.n_agents)}
    
    # A straight line program is an exchange of goods    
    def straight_line(self, n_instr:int) -> dict:
        pass 
    
    # A smart execution is a good exchange where an agent's goods is modified sequentially and left unchanged
    def smart_execution(self, n_instr:int) -> dict:
        pass
    
    # An approximate exchange is an exchange where we are interested in all the goods of all the agents
    def approximate_exchange(self, n_instr:int) -> dict:
        pass
    
class Sort(object):
    def __init__(self, n_objects:int):
        self.n_objects = n_objects
        
    def sort_challenge(self) -> dict:
        pass 
    
        