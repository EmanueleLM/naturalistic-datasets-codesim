import copy as cp
import json
import os
import random 
import string 
from pydantic.json import pydantic_encoder
from abc import ABC, abstractmethod

from .my_types import Sample
class Problem(ABC):
    def __init__(self, name:str):
        self.name = name
        self.data: list[Sample] = []
        

    @abstractmethod
    def to_file(self) -> None:
        pass

    @abstractmethod        
    def _accumulate(self) -> Sample:
        pass

    def reset(self) -> None:
        self.data = []

    def generate_data(self, n_programs=1) -> dict:
        for _ in range(n_programs):
            new_sample = self._accumulate()
            self.data.append(new_sample)

    def dump_data_or_throw(self, path:str) -> None:
        try:
            with open(path, 'w') as f:
                json.dump(self.data, f, indent=4, default=pydantic_encoder)
        except Exception as e:
            raise ValueError(e)

    
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
        self.max_tradable = 10  # max value to add to a variable
        self.basepath = "./data/StraightLine/"
        
    def reset(self, n_ops:int=None, n_vars:int=None, n_instances:int=None) -> None:
        super().reset()
        self.n_ops = (n_ops if n_ops is not None else self.n_ops)
        self.vars = (n_vars if n_vars is not None else self.vars)
        self.instances = (n_instances if n_instances is not None else self.instances)
            
    def to_file(self, suffix:str="") -> None:
        os.makedirs(self.basepath, exist_ok=True)
        filename = f"n_ops-{self.n_ops}_n_vars-{self.vars}_n_instances-{self.instances}"
        filename += ".json" if suffix == "" else f"_{suffix}.json"
        path = self.basepath + filename
        self.dump_data_or_throw(path)

    def _accumulate(self):
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
        gt_syn = {}
        for ag in agents:
            for idx in agents[ag]:
                gt_syn[f"{ag}{idx}"] = agents[ag][idx]
        gt_nat = {ag: {f"obj-{k}":v for k,v in agents[ag].items()} for ag in agents}

        return Sample(syn=program, nat=prompt, label_syn=gt_syn, label_nat=gt_nat)

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
        self.basepath = "./data/CriticalPath/"
        
    def reset(self, n_ops:int=None, n_vars:int=None, len_critical_path:int=None) -> None:
        super().reset()
        self.n_ops = (n_ops if n_ops is not None else self.n_ops)
        self.vars = (n_vars if n_vars is not None else self.vars)
        self.critical_path = (len_critical_path if len_critical_path is not None else self.critical_path)
            
    def to_file(self, suffix:str="") -> None:
        os.makedirs(self.basepath, exist_ok=True)
        filename = f"n_ops-{self.n_ops}_n_vars-{self.vars}_len_critical_path-{self.critical_path}"
        filename += ".json" if suffix == "" else f"_{suffix}.json"
        path = self.basepath + filename
        self.dump_data_or_throw(path)
    
    def _accumulate(self):
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
Each of them has either a positive or a negative amount of money. If it is positve, it is a credit; if it is negative, it is a debit.
Here is the amount of money each agent has: {'; '.join([f'a{i}={random.randint(-10, 10)}' for i in range(v)])}.
The agents can exchange quantities of debit or credit among them. Here's the two possibilities:
1) An agent doubles the amount of credit (positive) or debit (negative) another agent has. The first agent loses the quantity the other agent had, while the second agent dounbles his credit or debit.
2) An agent gets all the credit (positive) or debit (negative) another agent has. The second agent has then zero money.
Here's a list of interactions between the agents.
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
                prompt += f"{src} doubles the amount of credit (positive) or debit (negative) {dst} has. {src} decreases or increases their amount of money accordingly\n"
            else:
                prompt += f"{src} gets all the credit (positive) or debit (negative) {dst} has. {dst} has no money now.\n"
                
            # TODO: integrate this code to the final version
            line_1 = line.replace('@1@', src).replace('@2@', dst)
            line_2 = (f"{dst} = 0" if '+' in op else f"{dst} *= 2")
                
            program += line_1 + '\n' + line_2 + '\n'
            # print(f"{i}: {line}")
            
        # Compute the ground truth
        exec(program)
        gt_syn = {variables[-1]: eval(variables[-1])}
        
        sample = Sample(syn=program, nat=prompt, label_syn=gt_syn, label_nat=gt_syn)
        return sample

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
        self.basepath = "./data/Loops/"
        
    def reset(self, 
              n_loops:int=None, 
              n_noisy_loops:int=None, 
              min_loop_length:int=None, 
              max_loop_length:int=None) -> None:
        super().reset()
        self.n_loops = (n_loops if n_loops is not None else self.n_loops)
        self.n_noisy_loops = (n_noisy_loops if n_noisy_loops is not None else self.n_noisy_loops)
        self.min_loop_length = (min_loop_length if min_loop_length is not None else self.min_loop_length)
        self.max_loop_length = (max_loop_length if max_loop_length is not None else self.max_loop_length)
        
        
    def to_file(self, suffix:str="") -> None:
        os.makedirs(self.basepath, exist_ok=True)
        filename = f"n_loops-{self.n_loops}_n_noisy_loops-{self.n_noisy_loops}_min_loop_length-{self.min_loop_length}_max_loop-{self.max_loop_length}"
        filename += ".json" if suffix == "" else f"_{suffix}.json"
        path = self.basepath + filename
        self.dump_data_or_throw(path)

    def _accumulate(self):
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
        

        sample = Sample(syn=program, nat=prompt, label_syn=gt_syn, label_nat=gt_nat)
        return sample
    
class Sort(Problem):
    def __init__(self, 
                 n_vars:int,
                 ascending:bool=True):
        
        super().__init__(name='Sort')
        assert n_vars > 1
        self.n_vars = n_vars
        self.ascending = ascending
        self.basepath = "./data/Sort/"
        self.algorithm = """def f(arr):
    n = len(arr)
    for j in range(1, n):
        val = arr[j]
        i = j - 1
        while i >= 0 and val {condition} arr[i]:
            arr[i + 1] = arr[i]
            i -= 1
        arr[i + 1] = val
    return arr"""
        
    def reset(self, n_vars:int=None, ascending:bool=None) -> None:
        super().reset()
        self.n_ops = (n_vars if n_vars is not None else self.n_vars)
        self.ascending = (ascending if ascending is not None else self.ascending)
            
    def to_file(self, suffix:str="") -> None:
        os.makedirs(self.basepath, exist_ok=True)
        filename = f"n_vars-{self.n_vars}_ascending-{self.ascending}"
        filename += ".json" if suffix == "" else f"_{suffix}.json"
        path = self.basepath + filename
        self.dump_data_or_throw(path)
        
    def _accumulate(self):
        """
        Creates a list of n unique numbers and asks the position of the k-greatest/smallest.
        """
        weights = random.sample(range(self.n_vars*10), self.n_vars)
        var2val = {f"obj-{i}":w for i,w in enumerate(weights)}
        val2var = {v:k for k,v in var2val.items()}
        prompt = f"""One has the following {self.n_vars} objects: {list(var2val)}.\n
This is the weight of each object in Kg: {var2val}.\n
"""
        program = f"""Here's a list of numbers. x = {list(var2val.values())}\n
Simulate the following algorithm with the list of numbers as input:\n
{self.algorithm.format(condition='<' if self.ascending else '>')}
"""  # revert condition is bubble-sort, i.e., condition='>' if self.ascending else '<'
        k = random.randint(0, self.n_vars-1)
        weights.sort(reverse=not(self.ascending))
        gt_syn = {'position': k,
                'label': weights[k],
                'ascending': self.ascending}
        gt_nat = {'position': k+1, 
                  'label': val2var[weights[k]],
                  'ascending': self.ascending}
                  
        sample = Sample(syn=program, nat=prompt, label_syn=gt_syn, label_nat=gt_nat)
        return sample
        
        