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

def experiment(samples: list[Sample], model: str, op_type: OperationType):
    correct_nat = 0
    correct_syn = 0
    for sample in samples:
        query_syn, query_nat = format_query(sample, op_type)
        result = get_answer(query_syn.prompt, model)
        print(query_syn.answer, result, query_syn.answer == result)
        if result == query_syn.answer:
            correct_syn += 1

        result = get_answer(query_nat.prompt, model)
        if result == query_nat.answer:
            correct_nat += 1


    print(f"Correct Natural: {correct_nat}/{len(samples)}")
    print(f"Correct Syntax: {correct_syn}/{len(samples)}")

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

        case OperationType.critical_path:

            SL = prompt.CriticalPath
            question_syn = SL.questions_syn[0].format(varname=sample.label_syn)
            question_nat = SL.questions_nat[0].format(varname=sample.label_nat)

            var_name = list(sample.label_syn.keys())[0]  # can sample here
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

        case _:
            raise ValueError("Operation Type not supported")

def get_answer(prompt: str, model: str):
    def query_engine(prompt: str):
        return utils.queryLLM(prompt, model)

    answer = query_engine(prompt)

    # now extract content in between the last occurrence of answer tags
    start = answer.rfind("<answer>")
    end = answer.rfind("</answer>")
    
    if start == -1 or end == -1:
        return ""

    return answer[start+8:end]

if __name__ == "__main__":
    main()


