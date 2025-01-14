"""
This is a short CLI program to start the experiments for the CodeSimulation project.

You should support 5 types of operations
- critical-path
- parallel-paths
- straight-line
- nested-loop
- sorting

You also get the path of the dataset as an argument.
"""

import json
import argparse
import random
import csv
from pydantic import BaseModel
from . import utils

from .my_types import Sample, OperationType
from . import prompt

# Used to map obj-1 and similars to a string.
g_object_map = dict()

class PromptAndCheck(BaseModel):
    prompt: str
    answer: str

def main():
    parser = argparse.ArgumentParser(description="Start experiments for the CodeSimulation project.")
    parser.add_argument('-o', '--operation', choices=['kim-schuster', 'critical-path', 'parallel-paths', 'straight-line', 'nested-loop', 'sorting'], 
                        help='Type of operation to perform')
    parser.add_argument('-d', '--dataset_path', type=str, help='Path of the dataset')
    parser.add_argument('-m', '--model', type=str, help='Model to use for the experiment')

    args = parser.parse_args()

    print(f"Operation: {args.operation}")
    print(f"Dataset Path: {args.dataset_path}")

    load_and_sample_objects()
    print(f"Objects Sampled: {g_object_map}")

    op_type: OperationType = OperationType(args.operation)
    # Load the dataset as json
    samples = []
    with open(args.dataset_path, 'r') as f:
        allfile = f.read()
        jsondata = json.loads(allfile)

        for sample in jsondata:
            # print(sample)
            samples.append(Sample(**sample))
            break

    # print(samples[0])
    # send_request(samples[0])

    # print(format_query(samples[0], op_type))
    experiment(samples, args.model, op_type)

def load_and_sample_objects():
    global g_object_map
    file = "./data/objects_with_bnc_frequency.csv"

    sample_freq = dict()
    # read and load csv file, has two columns, name and frequency, we need to use sample categorically using the frequency
    with open(file, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip the headers
        for row in reader:
            sample_freq[row[0]] = int(row[1])

    # k is choosen arbitrarily, but we need the maximum number of objects anyways.
    sampled_objects = random.choices(list(sample_freq.keys()), k=10, weights=list(sample_freq.values()))
    g_object_map = {i: obj for i, obj in enumerate(sampled_objects)}


def experiment(samples: list[Sample], model: str, op_type: OperationType):
    correct_nat = 0
    correct_syn = 0
    for sample in samples:
        query_syn, query_nat = format_query(sample, op_type)
        print(query_syn)
        print(query_nat)
        result = get_answer(query_syn.prompt, model)
        if result == query_syn.answer:
            correct_syn += 1

        result = get_answer(query_nat.prompt, model)
        if result == query_nat.answer:
            correct_nat += 1


    print(f"Correct Natural: {correct_nat}/{len(samples)}")
    print(f"Correct Syntax: {correct_syn}/{len(samples)}")

def substitute_objects(string: str, prefix="obj-"):
    for i in g_object_map:
        string = string.replace(prefix + str(i), g_object_map[i])

    return string

def format_query(sample: Sample, op_type: OperationType) -> tuple[PromptAndCheck, PromptAndCheck]:
    match op_type:
        case OperationType.kim_schuster:
            first_key = list(sample.label_syn.keys())[0]
            question = prompt.Boxes.questions_syn[0].format(varname=f"x{first_key}")
            prompt_syn = prompt.Boxes.user_cot.format(prefix="Here's some code:", 
                                            problem=sample.syn, 
                                            question=question)

            first_key = list(sample.label_nat.keys())[0]
            question = prompt.Boxes.questions_nat[0].format(varname=f"box {first_key}")
            prompt_nat = prompt.Boxes.user_cot.format(prefix="",
                                            problem=sample.nat,
                                            question=question)
            
            return (PromptAndCheck(prompt=prompt_syn, answer=f"{', '.join([str(x) for x in sample.label_syn[first_key]])}"),
                    PromptAndCheck(prompt=prompt_nat, answer=f"{', '.join(sample.label_nat[first_key])}"))

        case OperationType.straight_line:
            var_name = random.choice(list(sample.label_syn.keys()))
            question = prompt.StraightLine.questions_syn[0].format(varname=var_name)
            prompt_syn = prompt.StraightLine.user_cot.format(prefix="Here's some code:",
                                                            problem=sample.syn,
                                                            question=question)
            
            agent_name = random.choice(list(sample.label_nat.keys()))
            object_name = random.choice(list(sample.label_nat[agent_name].keys()))
            question = prompt.StraightLine.questions_nat[0].format(varname=object_name, agentname=agent_name)
            prompt_nat = prompt.StraightLine.user_cot.format(prefix="",
                                                            problem=sample.nat,
                                                            question=question)
            prompt_nat = substitute_objects(prompt_nat)

            return (PromptAndCheck(prompt=prompt_syn, answer=str(sample.label_syn[var_name])),
                    PromptAndCheck(prompt=prompt_nat, answer=substitute_objects(str(sample.label_nat[agent_name][object_name]))))

        case OperationType.critical_path:
            var_name = random.choice(list(sample.label_syn.keys()))
            question = prompt.CriticalPath.questions_syn[0].format(varname=var_name)
            prompt_syn = prompt.CriticalPath.user_cot.format(prefix="Here's some code:",
                                                            problem=sample.syn,
                                                            question=question)
            
            agent_name = random.choice(list(sample.label_nat.keys()))
            question = prompt.CriticalPath.questions_nat[0].format(agentname=agent_name)
            prompt_nat = prompt.CriticalPath.user_cot.format(prefix="",
                                                            problem=sample.nat,
                                                            question=question)
            
            return (PromptAndCheck(prompt=prompt_syn, answer=sample.label_syn[var_name]),
                    PromptAndCheck(prompt=prompt_nat, answer=sample.label_nat[agent_name]))

        case OperationType.parallel_paths:
            var_names = list(sample.label_syn.keys())
            question = prompt.ParallelPaths.questions_syn[0].format(varnames=", ".join(var_names))
            prompt_syn = prompt.ParallelPaths.user_cot.format(prefix="Here's some code:",
                                                            problem=sample.syn,
                                                            question=question)
            
            agent_names = list(sample.label_nat.keys())
            object_names = list(sample.label_nat[agent_names[0]].keys())
            question = prompt.ParallelPaths.questions_nat[0].format(varnames=object_names,
                                                                agentnames=agent_names)
            prompt_nat = prompt.ParallelPaths.user_cot.format(prefix="",
                                                            problem=sample.nat,
                                                            question=question)
            
            return (PromptAndCheck(prompt=prompt_syn, answer=f"{', '.join([str(x) for x in sample.label_syn.values()])}"),
                    PromptAndCheck(prompt=prompt_nat, answer=f"{', '.join([str(x) for x in sample.label_nat.values()])}"))

        case OperationType.nested_loop:
            # TODO: bisogna ancora fare il sampling degli oggetti naturali qui.
            first_key = list(sample.label_syn.keys())[0]
            question = prompt.Loops.questions_syn[0].format(varname=first_key)
            prompt_syn = prompt.Loops.user_cot.format(prefix="Here's some code:",
                                                    problem=sample.syn,
                                                    question=question)
            
            key_val = list(sample.label_nat.keys())[0]
            content, box = key_val.split(" in ")
            question = prompt.Loops.questions_nat[0].format(varname=content, varname_origin=box)
            prompt_nat = prompt.Loops.user_cot.format(prefix="",
                                                    problem=sample.nat,
                                                    question=question)
            
            return (PromptAndCheck(prompt=prompt_syn, answer=sample.label_syn[first_key]),
                    PromptAndCheck(prompt=prompt_nat, answer=sample.label_nat[key_val]))

        case OperationType.sorting:
            position = sample.label_syn["position"]
            ascending = sample.label_syn["ascending"]
            question = prompt.Sort.questions_syn[0].format(k=position, heavy = "heavy" if ascending else "light")
            prompt_syn = prompt.Sort.user_cot.format(prefix="Here's some code:",
                                                    problem=sample.syn,
                                                    question=question)
            
            agent_name = random.choice(list(sample.label_nat.keys()))
            object_name = random.choice(list(sample.label_nat[agent_name].keys()))
            question = prompt.Sort.questions_nat[0].format(k=position, biggest_smallest= "biggest" if ascending else "smallest")
            prompt_nat = prompt.Sort.user_cot.format(prefix="",
                                                    problem=sample.nat,
                                                    question=question)
            
            return (PromptAndCheck(prompt=prompt_syn, answer=sample.label_syn["label"]),
                    PromptAndCheck(prompt=prompt_nat, answer=sample.label_nat["label"]))

        case _:
            raise ValueError("Operation Type not supported")

def get_answer(prompt: str, model: str):
    def query_engine(prompt: str):
        return utils.queryLLM(prompt, model)

    answer = query_engine(prompt)
    print(answer)
    # now extract content in between the last occurrence of answer tags
    start = answer.rfind("<answer>")
    end = answer.rfind("</answer>")
    
    if start == -1 or end == -1:
        return ""

    return answer[start+8:end]

if __name__ == "__main__":
    main()


