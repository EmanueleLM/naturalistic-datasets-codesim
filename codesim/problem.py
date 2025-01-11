import copy as cp
import json
import os
import random 
import string 
from abc import ABC, abstractmethod

class Problem(ABC):
    def __init__(self, name:str):
        self.name = name
        
    @abstractmethod
    def reset(self) -> None:
        pass
        
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
        self.max_tradable = 10  # max value to add to a variable
        self.basepath = "./data/StraightLine/"
        
    def reset(self, n_ops:int=None, n_vars:int=None, n_instances:int=None) -> None:
        self.n_ops = (n_ops if n_ops is not None else self.n_ops)
        self.vars = (n_vars if n_vars is not None else self.vars)
        self.instances = (n_instances if n_instances is not None else self.instances)
        self.data = {}
        self.idx = 0
            
    def generate_data(self, n_programs:int=1) -> dict:
        for idx in range(self.idx+n_programs):
            syn, nat, gt_syn, gt_nat = self.__accumulate()
            self.data[idx] = {
                'syn': syn,
                'nat': nat,
                'label-syn': gt_syn,
                'label-nat': gt_nat
            }
        self.idx += n_programs
            
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
        prompt += """\nHere's the list of potential interactions between agents.
An agent can give a quantity of one their objects to another agent. 
In that case, they lose that quantity of that object and the other agent increases theirs'.
An agent can lose some or all of their objects. In that case, they lose that quantity of that object.
An agent can buy some quantity of an object. In that case, they increase the quantity of that object.
Here's a list of interactions between the agents.
"""
        
        program = ''
        for ag in agents:
            program += '; '.join([f'{ag}{i}={agents[ag][i]}' for i in range(o)]) + '\n'
        
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
                    qt = random.randint(1, self.max_tradable)
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
                qt = random.randint(1, self.max_tradable)
                program += f"{v1}{ob} += {qt}\n"
                agents[v1][ob] += qt
                prompt += f"Agent-{v1} buys {qt} obj-{ob}.\n"
            # print(program)
            
        # Generate the syn and naturalistic labels
        gt_syn = agents
        gt_nat = {ag: {f"obj-{k}":v for k,v in agents[ag].items()} for ag in agents}

        return program, prompt, gt_syn, gt_nat

class CriticalPath(Problem):
    def __init__(self, 
                 n_ops:int,
                 n_vars:int, 
                 len_critical_path:int):
        """
        n_ops:int, the number of operations returned
        n_vars:int, the number of variables declared in the code (%2==0 and >1)
        len_critical_path:int, the length of the critical path of the last variable of the program
        """
        super().__init__(name='CriticalPath')
        assert n_vars > 1 and n_ops >= len_critical_path
        self.n_ops = n_ops
        self.vars = (n_vars if n_vars%2==0 else n_vars+1)  # must be even
        self.critical_path = len_critical_path
        self.data = {}
        self.idx = 0
        self.basepath = "./data/CriticalPath/"
        
    def generate_data(self, n_programs:int=1) -> dict:
        for idx in range(self.idx+n_programs):
            syn, nat, gt_syn = self.__accumulate()
            self.data[idx] = {
                'syn': syn,
                'nat': nat,
                'label-syn': gt_syn,
                'label-nat': gt_syn
            }
        self.idx += n_programs
        
    def reset(self, n_ops:int=None, n_vars:int=None, len_critical_path:int=None) -> None:
        self.n_ops = (n_ops if n_ops is not None else self.n_ops)
        self.vars = (n_vars if n_vars is not None else self.vars)
        self.critical_path = (len_critical_path if len_critical_path is not None else self.critical_path)
        self.data = {}
        self.idx = 0
            
    def to_file(self, suffix:str="") -> None:
        os.makedirs(self.basepath, exist_ok=True)
        filename = f"n_ops-{self.n_ops}_n_vars-{self.vars}_len_critical_path-{self.critical_path}"
        filename += ".json" if suffix == "" else f"_{suffix}.json"
        path = self.basepath + filename
        try:
            json.dump(self.data, open(path, 'w'), indent=4)
        except Exception as e:
            raise ValueError(e)
    
    def __accumulate(self) -> dict:
        """
        This function creates a program of length n and with v variables connected by simple binary operations.
        The last variable is used only in portion of the program of length c, so that the program has a critical path for the last variable of length c.
        """
        n = self.n_ops; v = self.vars; c = self.critical_path  # TODO: delete this line and make the code work
        assert n >= 0 and isinstance(n, int)
        assert c <= n and isinstance(c, int)

        ops = ['@1@ -= @2@', '@1@ += @2@']
        variables = [f'a{i}' for i in range(v)]
        v_ind = int(v//2)
        
        prompt = f"""There are {v} agents, {[f'a{i}' for i in range(v)]}. 
Each of them has either a credit, which we represent as a negative amount of money other agents owe him,
or a debit, i.e., a positive quantity of money he ows to the other agents. 
Here is the amount of credit/debit each agent has: {'; '.join([f'a{i}={random.randint(-10, 10)}' for i in range(v)])}.
Here's the list of potential interactions between agents.
An agent can borrow money from another agent. 
In that case, the first agent increases his total amount while the other decreases it of the same quantity.
An agent can loan some of his money. 
In that case, the first agent decreases his total amount while the other increases it of the same quantity.
An agent can increase his debit by buying things. In that case, he is the only one affected.
Here's a list of real interactions between the agents.
"""

        program = ''
        program = '; '.join([f'a{i}={random.randint(-10, 10)}' for i in range(v)]) + '\n'
        # print(program)
        if n!=c:
            start_inj = random.choice([i for i in range(0, n-c)])
        else:
            start_inj = 0
        end_inj = start_inj + c
        # print(f"Critical path start:{start_inj}, end:{end_inj-1}")
        for i in range(n):
            op = random.choice(ops)
            line = cp.deepcopy(op)
            if i<start_inj:  # src is any independent variable
                src = random.choice(variables)
                if '-' in op:  # avoid operation ai -= ai 
                    set_dst = (set(variables[:v_ind]) if isinstance(variables[:v_ind], list) else set([variables[:v_ind]]))
                    dst = random.choice(list(set_dst - set([src])))
                else:
                    dst = random.choice(variables[:v_ind])

            elif i>end_inj:  # src is any variable (except for the last one)
                src = random.choice(variables)
                if '-' in op:  # avoid operation ai -= ai 
                    set_dst = (set(variables[:-1]) if isinstance(variables[:-1], list) else set([variables[:-1]]))
                    dst = random.choice(list(set_dst - set([src])))
                else:
                    dst = random.choice(variables[:-1])

            elif i==start_inj or i==end_inj-1:
                src = random.choice(variables[v_ind:])
                if '-' in op:  # avoid operation ai -= ai 
                    set_dst = (set(variables[v_ind:]) if isinstance(variables[v_ind:], list) else set([variables[v_ind:]]))
                    dst = random.choice(list(set_dst - set([src])))
                else:
                    dst = random.choice(variables[v_ind:])
                
            else:  # start_inj <= i <= end_inj:
                if random.random() > 0.3:
                    src =  random.choice(variables[v_ind:])
                    if '-' in op:  # avoid operation ai -= ai 
                        # print(src)
                        # print(list(set(variables[v_ind:]) - set([src])))
                        set_dst = (set(variables[v_ind:]) if isinstance(variables[v_ind:], list) else set([variables[v_ind:]]))
                        dst = random.choice(list(set_dst - set([src])))
                    else:
                        dst = random.choice(variables[v_ind:])
                else:
                    dst = variables[-1]
                    if '-' in op:  # avoid operation ai -= ai 
                        set_src = (set(variables[v_ind:]) if isinstance(variables[v_ind:], list) else set([variables[v_ind:]]))
                        src = random.choice(list(set_src - set([dst])))
                    else:
                        src = random.choice(variables[v_ind:])
                        
            # Nat prompt 
            if '-' in op:
                prompt += f"{src} loans all his money to {dst}.\n"
            else:
                prompt += f"{src} borrows all the money {dst} has.\n"
                
            line = line.replace('@1@', dst).replace('@2@', src)
            # print(f"{i}: {line}")
            program += line + '\n'
            
        # Compute the ground truth
        exec(program)
        gt_syn = {variables[-1]: eval(variables[-1])}
        
        return program, prompt, gt_syn

class ParallelPaths(StraightLine):
    def __init__(self, 
                 n_ops:int, 
                 n_vars:int, 
                 n_instances:int):
        
        super().__init__(n_ops, n_vars, n_instances)
        self.name = "ParallelPaths"
        self.basepath = "./data/ParallelPaths/"
        
class Loops(Problem):
    def __init__(self, 
                 n_loops:int, 
                 n_noisy_loops:int,
                 min_loop_length:int=1,
                 max_loop_length:int=10):
        
        super().__init__(name='Loops')
        assert n_loops > n_noisy_loops >= 0
        self.n_loops = n_loops
        self.n_noisy_loops = n_noisy_loops
        self.min_loop_length = min_loop_length
        self.max_loop_length = max_loop_length
        self.data = {}
        self.idx = 0
        self.basepath = "./data/Loops/"
        
    def reset(self, 
              n_loops:int=None, 
              n_noisy_loops:int=None, 
              min_loop_length:int=None, 
              max_loop_length:int=None) -> None:
        self.n_loops = (n_loops if n_loops is not None else self.n_loops)
        self.n_noisy_loops = (n_noisy_loops if n_noisy_loops is not None else self.n_noisy_loops)
        self.min_loop_length = (min_loop_length if min_loop_length is not None else self.min_loop_length)
        self.max_loop_length = (max_loop_length if max_loop_length is not None else self.max_loop_length)
        self.data = {}
        self.idx = 0
        
    def generate_data(self, n_programs:int=1) -> dict:
        for idx in range(self.idx+n_programs):
            syn, nat, gt_syn, gt_nat = self.__accumulate()
            self.data[idx] = {
                'syn': syn,
                'nat': nat,
                'label-syn': gt_syn,
                'label-nat': gt_nat
            }
        self.idx += n_programs
        
    def to_file(self, suffix:str="") -> None:
        os.makedirs(self.basepath, exist_ok=True)
        filename = f"n_loops-{self.n_loops}_n_noisy_loops-{self.n_noisy_loops}_min_loop_length-{self.min_loop_length}_max_loop-{self.max_loop_length}"
        filename += ".json" if suffix == "" else f"_{suffix}.json"
        path = self.basepath + filename
        try:
            json.dump(self.data, open(path, 'w'), indent=4)
        except Exception as e:
            raise ValueError(e)

    def __accumulate(self) -> dict:
        c = self.n_loops; cn = self.n_noisy_loops
        set_c = [i for i in range(c)]
        set_nc = random.sample(set_c, cn)
        loops = {i:(i not in set_nc) for i in range(c)}  # True, the loop is necessary for the ground truth
        
        # Naturalistic objects 
        nat_objects = ["obj-gen"] + [f"obj-{i}" for i in set(set_c).difference(set_nc)]
        nat_noisy_objects = [f"nobj-{i}" for i in set_nc]
        ptr_nat, ptr_noisy_nat = 1, 0  # pointer to the first var in set_c and set_nc
        prompt = f"Here's a situation.\n"
        
        program = '; '.join([f"n_{i}=0" for i in set_c]) + '\n'
        n_tabs = 0
        for idx, is_necessary in loops.items():
            tabs_decl = '\t'*(n_tabs)
            tabs_body = '\t'*(n_tabs+1)
            
            k = random.randint(self.min_loop_length, self.max_loop_length)
            program += tabs_decl + f"for _ in range({k}):\n"
            program += tabs_body + f"n_{idx} += 1\n"
            
            if is_necessary:
                n_tabs += 1
                prompt += f"There are {k} {nat_objects[ptr_nat]} in {nat_objects[ptr_nat-1]}.\n"
                ptr_nat += 1
            else:
                prompt += f"There are {k} {nat_noisy_objects[ptr_noisy_nat]} in {nat_objects[ptr_nat-1]}.\n"
                ptr_noisy_nat += 1
        
        # Generate the ground truth label
        exec(program)
        gt = eval(f"n_{set_c[-1]}")
        gt_syn = {f"n_{set_c[-1]}": gt}
        gt_nat = {f"obj-{set_c[-1]} in obj-gen": gt}
        
        return program, prompt, gt_syn, gt_nat
    
class Sort(Problem):
    def __init__(self, 
                 n_objects:int):
        
        super().__init__(name='Sort')
        pass
        
    def generate_data(n:int, a:int, o:int, cp:int) -> dict:
        pass 
        
    def to_file(self) -> None:
        pass
    
        