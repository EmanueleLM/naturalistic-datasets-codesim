from dataclasses import dataclass

@dataclass
class System:
    messages = [
        "You are a helpful and honest assistant.",
        "You are a reliable and straightforward assistant. Respond accurately."
    ]
    
@dataclass 
class StraightLine:
    user_cot = """{prefix}
{problem}
{question}
Think step by step and provide the answer between <answer></answer> tags.
For example, reply with <answer>1</answer> if the answer is 1.
"""
    
    questions_syn = ["What is the value of {varname} at the end of the computation?"]
    questions_nat = ["How many {varname} does agent {agentname} has at the end?"]
    
@dataclass 
class CriticalPath:
    user_cot = """{prefix}
{problem}
{question}
Think step by step and provide the numerical answer between <answer></answer> tags.
For example, reply with <answer>1</answer> if the answer is 1.
"""
    
    questions_syn = ["What is the value of {varname} at the end of the computation?"]
    questions_nat = ["How much money does {agentname} has at the end?"]
    
@dataclass 
class ParallelPaths:
    user_cot = """{prefix}
{problem}
{question}
Think step by step and provide the answer as a list of integers between <answer></answer> tags.
For example, reply with <answer>[3, 5, 1]</answer>.
"""
    
    questions_syn = ["What is the value of {varnames} at the end of the computation? Report them in the order they were declared."]
    questions_nat = ["How many objects does each agent have at the end? Report them in the order they were declared."]

    
@dataclass 
class Loops:
    user_cot = """{prefix}
{problem}
{question}
Think step by step and provide the numerical answer between <answer></answer> tags.
For example, reply with <answer>1</answer> if the answer is 1.
"""
    
    questions_syn = ["What is the value of {varnames} at the end of the computation?"]
    questions_nat = ["How many {varname} are in a {varname_origin}?"]

  
@dataclass 
class Sort:
    user_cot = """{prefix}
{problem}
{question}
Think step by step and provide the numerical answer between <answer></answer> tags.
For example, reply with <answer>1</answer> if the answer is 1.
"""
    
    questions_nat = ["What is the value of {k}-th {biggest_smallest} object?"]
    questions_syn = ["What is the value of {k}-th most {heavy} object?"]
    