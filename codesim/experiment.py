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
from pydantic import BaseModel
from . import utils

from .my_types import Sample, OperationType
from . import prompt

def main():
    parser = argparse.ArgumentParser(description="Start experiments for the CodeSimulation project.")
    parser.add_argument('-o', '--operation', choices=['kim-schuster', 'critical-path', 'parallel-paths', 'straight-line', 'nested-loop', 'sorting'], 
                        help='Type of operation to perform')
    parser.add_argument('-d', '--dataset_path', type=str, help='Path of the dataset')
    parser.add_argument('-m', '--model', type=str, help='Model to use for the experiment')

    args = parser.parse_args()

    print(f"Operation: {args.operation}")
    print(f"Dataset Path: {args.dataset_path}")

    op_type: OperationType = OperationType(args.operation)
    # Load the dataset as json
    samples = []
    with open(args.dataset_path, 'r') as f:
        allfile = f.read()
        jsondata = json.loads(allfile)

        for i in jsondata:
            sample = jsondata[i]
            print(sample)
            samples.append(Sample(**sample))
            break

    # print(samples[0])
    # send_request(samples[0])

    experiment(samples, args.model, op_type)




def experiment(samples: list[Sample], model: str, op_type: OperationType):
    for sample in samples:
        query = format_query(sample, op_type)
        result = send_request(sample)

def format_query(sample: Sample, op_type: OperationType):
    match op_type:
        case OperationType.kim_schuster:
            raise NotImplementedError
        case OperationType.critical_path:

            SL = prompt.CriticalPath
            question_syn = SL.questions_syn[0].format(varname=sample.label_syn)
            question_nat = SL.questions_nat[0].format(varname=sample.label_nat)

            var_name = list(sample.lab_syn.keys())[0]  # can sample here
            question = SL.questions_syn[0].format(varname=var_name)
            prompt_syn = SL.user_cot.format(prefix="Here's some code:", 
                                            problem=sample.syn, 
                                            question=question)


            agent_name = list(sample.lab_nat.keys())[0]  # can sample here
            object_name = list(sample.lab_nat[agent_name].keys())[0]  # same...
            question = SL.questions_nat[0].format(varname=object_name, agentname=agent_name)
            prompt_nat = SL.user_cot.format(prefix="",
                                            problem=sample.syn,
                                            question=question)


def send_request(sample: Sample):
    pretext = """You are given a text, what is the value of the last variable? Wrap your output into <answer> </answer> tags."""
    query_engine = lambda prompt: utils.queryLLM(prompt, './config.json', 'gpt-4o-mini')

    syn_code = sample.syn
    query = pretext + syn_code

    answer = query_engine(query)
    print(answer)

if __name__ == "__main__":
    main()


