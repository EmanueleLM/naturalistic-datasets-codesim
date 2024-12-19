from dataclasses import dataclass

@dataclass
class System:
    messages = [
        "You are a helpful and honest assistant.",
        "You are a reliable and straightforward assistant. Respond accurately."
    ]
    
@dataclass 
class GoodExchange:
    user_cot = """
{problem}

{question}

Think step by step and provide the answer between <answer></answer> tags.
For example, reply with <answer>1</answer> if the answer is 1.
"""
    
    questions = ["What is the value of {varname} at the end of the computation?"]
    
@dataclass 
class ApproximateExchange:
    user_cot = """
{problem}

{question}

Think step by step and provide the answer between <answer></answer> tags.
For example, reply with <answer>[1, 0, 3]</answer> if the value of the goods is respectively 1, 0, and 3.
Provide the values in the order they are given at the beginning.
"""
    
    questions = ["What is the number of {varnames} {agents} have the end of the computation?"]
    
@dataclass 
class Sort:
    user_cot = """{name} has the following objects: {objects}.
Each object has the following weight: {weights}.
{name} wants to sort the objects in ascending order of weight.

{question}

Think step by step and provide the answer between <answer></answer> tags.
For example, if the object to order are 'shoes', 'mugs' and 'bananas', and their weight is respectively 5, 1 and 7,
reply with <answer>['mugs', 'shoes', 'banana']</answer>.
"""
    
    questions = ["How will {name} sort the objects in the correct order?"]
    