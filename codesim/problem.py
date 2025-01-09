import json
import os
import random 
import string 
from abc import ABC, abstractmethod

class Problem(ABC):
    def __init__(self, name:str):
        self.name = name
        self.basepath = "./data/"
        
    @abstractmethod
    def generate_data(self) -> dict:
        pass
    
    @abstractmethod
    def to_file(self) -> None:
        pass

class StraightLine(Problem):
    def __init__(self, 
                 n_ops:int, 
                 n_vars:int, 
                 n_instances:int):
        """
        n_ops:int, the number of operations returned in a program
        n_vars:int, the number of variables/agents
        n_instances:int, the number of unique objects instantiated per-var/agent
        """
        super().__init__(name='StraightLine')
        self.n_ops = n_ops
        self.vars = n_vars
        self.instances = n_instances
        self.data = {}
        self.idx = 0
        self.basepath = self.basepath + "StraightLine/"
        
    def reset(self, n_ops:int=None, n_vars:int=None, n_instances:int=None) -> None:
        self.n_ops = (n_ops if n_ops is not None else self.n_ops)
        self.vars = (n_vars if n_vars is not None else self.vars)
        self.instances = (n_instances if n_instances is not None else self.instances)
        self.data = {}
        self.idx = 0
        
    def generate_data(self, n_programs:int=1) -> dict:
        for _ in range(n_programs):
            self.idx += 1
            syn, nat = self.__accumulate()
            self.data[self.idx] = {
                'syn': syn,
                'nat': nat
            }
            
    def to_file(self, suffix:str="") -> None:
        os.makedirs(self.basepath, exist_ok=True)
        filename = f"n_ops-{self.n_ops}_n_vars-{self.vars}_n_instances-{self.instances}"
        filename += ".json" if suffix == "" else f"_{suffix}.json"
        path = self.basepath + filename
        try:
            json.dump(self.data, open(path, 'w'), indent=4)
        except Exception as e:
            raise ValueError(e)

    def __accumulate(self) -> dict:
        """
        Returns a dictionary with the following keys:
        - 'syn': a straight line code
        - 'nat': the naturalistic version of 'syn'
        - 'gt_syn': all the ground truth labels for 'syn'
        - 'gt_nat': all the ground truth labels for 'nat'
        """
        n = self.n_ops; a = self.vars; o = self.instances  # TODO: delete this line and make the code work
        assert n > 0 and isinstance(n, int)
        alphabet = string.ascii_lowercase
        agents = alphabet[:a]
        
        ops = ['@1-2-give-q@', '@1-buy-q@', '@1-lose-q@']
        agents = {ag:{i:random.randint(0, 10) for i in range(o)} for ag in agents}
        
        prompt = f"There are {a} agents, {[ag for ag in agents]}. Each of them has {o} items, {[f'obj-{ob}' for ob in range(o)]}.\n"
        prompt += "Here is the initial quantity of each object per agent.\n\n"
        for ag in agents:
            prompt += f"Agent-{ag} has "
            for ob in range(o):
                prompt += f"{agents[ag][ob]} obj-{ob}, "
            prompt = prompt[:-2] + ".\n"
        prompt += "\nHere's the list of potential interactions between agents.\n"
        prompt += f"An agent can give a quantity of one their objects to another agent. In that case, they lose that quantity of that object and the other agent increases theirs'.\n"  # Trade
        prompt += f"An agent can lose some or all of their objects. In that case, they lose that quantity of that object.\n"  # Lose
        prompt += f"An agent can buy some quantity of an object. In that case, they increase the quantity of that object.\n"  # Buy
        prompt += "Here's a list of real interactions between the agents. At the end of the interactions, I will ask you to tell me the exact quantity of an object a specific agent has.\n\n"
        
        program = ''
        for ag in agents:
            program += '; '.join([f'{ag}{i}={agents[ag][i]}' for i in range(o)]) + '\n'
        
        max_tradable = 5
        for _ in range(n):
            v1 = random.choice(list(agents.keys()))  # first agent
            # print(f"A1: {v1}")
            op = random.choice(ops)  # operation
            if all([ai>0 for ai in agents[v1].values()]):  # must have something to give or lose, otherwise use buy
                if op == '@1-2-give-q@':  # agent1 gives to agent2 quantity q of an object they have
                    # print("Trade")
                    set_agents = set(agents).difference(v1)
                    v2 = random.choice(list(set_agents))  # chose another agent
                    givable = [i for i in range(o) if agents[v1][i]>0] #  select an object v1 can give
                    to_give = random.choice(givable)
                    qt = random.randint(1, agents[v1][to_give])
                    if qt == agents[v1][to_give]:
                        program += f"{v2}{to_give} += {v1}{to_give}\n{v1}{to_give} -= {v1}{to_give}\n"
                        agents[v1][to_give] -= qt
                        agents[v2][to_give] += qt
                        assert agents[v1][to_give] >= 0
                        prompt += f"Agent-{v1} gives all their obj-{to_give} to agent-{v2}.\n"
                    else: 
                        program += f"{v2}{to_give} += {qt}\n{v1}{to_give} -= {qt}\n"
                        agents[v1][to_give] -= qt
                        agents[v2][to_give] += qt
                        prompt += f"Agent-{v1} gives {qt} obj-{to_give} to agent-{v2}.\n"
                        assert agents[v1][to_give] >= 0
                elif op == '@1-buy-q@':  # agent1 buys things
                    # print("Buy")
                    ob = random.randint(0, o-1)
                    qt = random.randint(1, max_tradable)
                    program += f"{v1}{ob} += {qt}\n"
                    agents[v1][ob] += qt
                    prompt += f"Agent-{v1} buys {qt} obj-{ob}.\n"
                else: # agent1 loses a quantity q of an object they have
                    # print("Lose")
                    # print("all", agents[v1])
                    givable = [i for i in range(o) if agents[v1][i]>0] #  select an object v1 can give
                    # print("givable", givable)
                    to_give = random.choice(givable)
                    qt = random.randint(1, agents[v1][to_give])
                    # print("togive", to_give)
                    # print("qt", qt)
                    if qt == agents[v1][to_give]:
                        program += f"{v1}{to_give} -= {v1}{to_give}\n" 
                        agents[v1][to_give] -= qt  
                        prompt += f"Agent-{v1} loses all their obj-{to_give}.\n"
                        assert agents[v1][to_give] >= 0
                    else:
                        program += f"{v1}{to_give} -= {qt}\n"   
                        agents[v1][to_give] -= qt
                        prompt += f"Agent-{v1} loses {qt} obj-{to_give}.\n" 
                        assert agents[v1][to_give] >= 0   
            else:  # only option is for agent1 to buy things
                # print("Buy-1")
                ob = random.randint(0, o-1)
                qt = random.randint(1, max_tradable)
                program += f"{v1}{ob} += {qt}\n"
                agents[v1][ob] += qt
                prompt += f"Agent-{v1} buys {qt} obj-{ob}.\n"
            # print(program)
        
        return program, prompt

class CriticalPath(Problem):
    def __init__(self, 
                 n_vars:int, 
                 instances_per_var:int, 
                 len_critical_path:int):
        
        super().__init__(name='CriticalPath')
        self.n_vars = self.n_agents = n_vars
        self.instances_per_var = self.n_goods = instances_per_var
        self.critical_path = len_critical_path
        
    def generate_data(n:int, a:int, o:int, cp:int) -> dict:
        pass 
        
    def to_file(self) -> None:
        pass

class ParallelPaths(Problem):
    def __init__(self, 
                 n_vars:int, 
                 instances_per_var:int, 
                 range_critical_paths:int):
        
        super().__init__(name='ParallelPaths')
        pass
        
    def generate_data(n:int, a:int, o:int, cp:int) -> dict:
        pass 
        
    def to_file(self) -> None:
        pass
    
class Loops(Problem):
    def __init__(self, 
                 n_vars:int, 
                 instances_per_var:int, 
                 range_critical_paths:int):
        
        super().__init__(name='Loops')
        pass

    def generate_data(n:int, a:int, o:int, cp:int) -> dict:
        pass 
        
    def to_file(self) -> None:
        pass
    
class Sort(Problem):
    def __init__(self, 
                 n_objects:int):
        
        super().__init__(name='Sort')
        pass
        
    def generate_data(n:int, a:int, o:int, cp:int) -> dict:
        pass 
        
    def to_file(self) -> None:
        pass
    
        