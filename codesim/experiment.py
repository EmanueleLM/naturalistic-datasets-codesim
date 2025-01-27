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

import datetime
import json
import argparse
import random
import csv
from pydantic import BaseModel
import pandas as pd
import os
import wandb
from pydantic.json import pydantic_encoder
import backoff
from . import utils

from .my_types import Sample, OperationType
from . import prompt

# Used to map obj-1 and similars to a string.
g_object_map = dict()

# Tables used to store the logs of the system.
g_has_wandb = False
g_nat_logs = None
g_syn_logs = None
# init wandb tables

class PromptAndCheck(BaseModel):
    prompt: str
    answer: str

class LogInfo(BaseModel):
    prompt: str
    label: str
    response: str
    full_response: str
    is_correct: bool

def main():
    global g_nat_logs
    global g_syn_logs
    global g_has_wandb

    parser = argparse.ArgumentParser(description="Start experiments for the CodeSimulation project.")
    parser.add_argument('-o', '--operation', choices=['kim-schuster', 'critical-path', 'parallel-paths', 'straight-line', 'nested-loop', 'sorting'], 
                        help='Type of operation to perform')
    parser.add_argument('-d', '--dataset_idx', default=-1,type=int, help='Index for the path of the dataset: -1 for all datasets')
    parser.add_argument("--dataset_path", type=str, help="Path to the dataset", default=None)
    parser.add_argument('-m', '--model', type=str, help='Model to use for the experiment')
    parser.add_argument('--wandb', action='store_true', help='Use wandb for logging, if not, use default txt file')

    args = parser.parse_args()
    g_has_wandb = args.wandb

    op_type: OperationType = OperationType(args.operation)
    dataset_base = get_dataset_path(op_type)
    dataset_list = []
    for dataset in os.listdir(dataset_base):
        if ".json" in dataset:
            dataset_list.append(os.path.join(dataset_base, dataset))
    dataset_list = sorted(dataset_list)

    if len(dataset_list) < args.dataset_idx:
        raise ValueError("Could node load dataset of the given index")
    elif args.dataset_idx >= 0:
        dataset_list = [dataset_list[args.dataset_idx]]
    
    if args.dataset_path is not None:
        print("Overwriting dataset list with the given path")
        dataset_list = [args.dataset_path]
        dataset_base = os.path.dirname(args.dataset_path)

    print(f"Operation: {args.operation}")
    print(f"Dataset Path: {args.dataset_idx}")

    load_and_sample_objects()
    print(f"Objects Sampled: {g_object_map}")

    for dataset_path in dataset_list:
        g_syn_logs = []
        g_nat_logs = []
        if g_has_wandb:
            wandb.init(project="codesim",
                config= {
                    "operation": args.operation,
                    "dataset_idx": args.dataset_idx,
                    "dataset_path": os.path.basename(dataset_path),
                    "model": args.model
                }
            )
            
        print("Running experiment for", dataset_path)
        # Load the dataset as json
        samples = []
        with open(dataset_path, 'r') as f:
            allfile = f.read()
            jsondata = json.loads(allfile)

            for sample in jsondata:
                # print(sample)
                samples.append(Sample(**sample))
                # break

        # print(samples[0])
        # send_request(samples[0])

        # print(format_query(samples[0], op_type))
        accuracy_nat, accuracy_syn = experiment(samples, args.model, op_type)
        save_results(accuracy_nat, accuracy_syn, args, os.path.basename(dataset_path))
        
        if g_has_wandb:
            wandb.log({"accuracy_nat": accuracy_nat, "accuracy_syn": accuracy_syn})
        # Log everything at the end

        if g_has_wandb:
            nat_table = wandb.Table(columns=["prompt", "label", "response", "full_response", "is_correct"])
            for log in g_nat_logs:
                nat_table.add_data(*log.model_dump().values())
                
            artifact = wandb.Artifact(f"nat-{args.operation}-{args.model}", type="dataset")
            artifact.add(nat_table, "results-nat")

            syn_table = wandb.Table(columns=["prompt", "label", "response", "full_response", "is_correct"])
            for log in g_syn_logs:
                syn_table.add_data(*log.model_dump().values())
            artifact_syn = wandb.Artifact(f"syn-{args.operation}-{args.model}", type="dataset")
            artifact_syn.add(syn_table, "results-syn")
            wandb.log_artifact(artifact)
            wandb.log_artifact(artifact_syn)

        # write to the logs
        basedir = os.path.join("logs", args.operation)
        os.makedirs(basedir, exist_ok=True)
        # date in yy-mm-dd-hh-mm
        date = datetime.datetime.now().strftime("%mM-%dD-%Hh-%Mm%Ss")
        with open(f"{basedir}/{os.path.basename(dataset_path)}-{args.model}-{date}.txt", 'w') as f:
            f.write("Natural Logs\n")
            json.dump(g_nat_logs, f, default=pydantic_encoder)
            f.write("\n")
            f.write(f"Accuracy: {accuracy_nat}")
            f.write("\n")
            f.write("Synthetic Logs\n")
            json.dump(g_syn_logs, f, default=pydantic_encoder)
            f.write("\n")
            f.write(f"Accuracy: {accuracy_syn}")
            f.write("\n")

        # close wandb
        if g_has_wandb:
            wandb.finish()

def save_results(accuracy_nat, accuracy_syn, args, dataset_name):
    basedir = os.path.join("results", args.operation)
    os.makedirs(basedir, exist_ok=True)
    
    filename = f"{basedir}/{args.model}.csv"
    curr_date = datetime.datetime.now().strftime("%mM-%dD-%Hh-%Mm%Ss")
    # check if the file exists
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        new_result = {
            "accuracy_nat": accuracy_nat, 
            "accuracy_syn": accuracy_syn, 
            "date": curr_date,
            "dataset": dataset_name
        }
        df = pd.concat([df, pd.DataFrame([new_result])], ignore_index=True)
        # order by dataset name and then date
        df = df.sort_values(by=["dataset", "date"])
        df.to_csv(filename, index=False)
    else:    
        df = pd.DataFrame([{
            "accuracy_nat": accuracy_nat, 
            "accuracy_syn": accuracy_syn, 
            "date": curr_date,
            "dataset": dataset_name
        }])
        df.to_csv(filename, index=False)
        

def get_dataset_path(operation: OperationType):
    base = "./data"
    match operation:
        case OperationType.kim_schuster:
            return f"{base}/boxes"
        case OperationType.critical_path:
            return f"{base}/CriticalPath"
        case OperationType.parallel_paths:
            return f"{base}/ParallelPaths"
        case OperationType.straight_line:
            return f"{base}/StraightLine"
        case OperationType.nested_loop:
            return f"{base}/Loops"
        case OperationType.sorting:
            return f"{base}/Sort"
        case _:
            raise ValueError("Operation Type not supported")

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

    random.seed(12) # so that is always the same
    # k is choosen arbitrarily, but we need the maximum number of objects anyways.
    sampled_objects = random.choices(list(sample_freq.keys()), k=10, weights=list(sample_freq.values()))
    g_object_map = {i: obj for i, obj in enumerate(sampled_objects)}

def compare_answers(answer: str, label: str, op_type):
    match op_type:
        case OperationType.kim_schuster:
            if label == "":
                return answer == "[]" or answer == "empty" or answer == "{}"
            
            answer = answer.lower()
            # remove parantesis if present
            if answer[0] in ["(", "[", "{"]:
                answer = answer[1:-1]
            
            answer_list = answer.split(", ")
            label_list = label.split(", ")
            return set(answer_list) == set(label_list)
            
        case _:
            return answer == label

def experiment(samples: list[Sample], model: str, op_type: OperationType):
    global g_nat_logs
    global g_syn_logs

    correct_nat = 0
    correct_syn = 0
    for sample in samples:
        query_syn, query_nat = format_query(sample, op_type)
        # print(query_syn.prompt)
        # print(query_nat.prompt)
        # print("Synthetic Answer:", query_syn.answer, query_nat.answer)
        syn_result, syn_whole_answer = get_answer(query_syn.prompt, model)
        if compare_answers(syn_result, query_syn.answer, op_type):
            correct_syn += 1

        nat_result, nat_whole_answer = get_answer(query_nat.prompt, model)
        if compare_answers(nat_result, query_nat.answer, op_type):
            correct_nat += 1

        # Log All
        syn_log = LogInfo(
            prompt=query_syn.prompt,
            label=query_syn.answer,
            response=syn_result,
            full_response=syn_whole_answer,
            is_correct=syn_result == query_syn.answer
        )

        nat_log = LogInfo(
            prompt=query_nat.prompt,
            label=query_nat.answer,
            response=nat_result,
            full_response=nat_whole_answer,
            is_correct=nat_result == query_nat.answer
        )

        g_syn_logs.append(syn_log)
        g_nat_logs.append(nat_log)

    print(f"Correct Natural: {correct_nat}/{len(samples)}")
    print(f"Correct Syntax: {correct_syn}/{len(samples)}")

    return correct_nat/len(samples), correct_syn/len(samples)

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
            
            return (PromptAndCheck(prompt=prompt_syn, answer=str(sample.label_syn[var_name])),
                    PromptAndCheck(prompt=prompt_nat, answer=str(sample.label_nat[agent_name])))

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
            prompt_nat = substitute_objects(prompt_nat)
            return (PromptAndCheck(prompt=prompt_syn, answer=f"[{', '.join([str(x) for x in sample.label_syn.values()])}]"),
                    PromptAndCheck(prompt=prompt_nat, answer=f"[{', '.join([str(value) for key in sample.label_nat for value in sample.label_nat[key].values()])}]"))  # flatten everything and only get numbers

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
            # no sense to substitute for nested loop, not all are containers.
            return (PromptAndCheck(prompt=prompt_syn, answer=str(sample.label_syn[first_key])),
                    PromptAndCheck(prompt=prompt_nat, answer=str(sample.label_nat[key_val])))

        case OperationType.sorting:
            position = sample.label_syn["position"]
            ascending = sample.label_syn["ascending"]
            question = prompt.Sort.questions_syn[0].format(k=position, heavy = "heavy" if ascending else "light")
            prompt_syn = prompt.Sort.user_cot.format(prefix="Here's some code:",
                                                    problem=sample.syn,
                                                    question=question)
            
            position = sample.label_nat["position"]
            question = prompt.Sort.questions_nat[0].format(k=position, biggest_smallest= "most light" if ascending else "most heavy")
            prompt_nat = prompt.Sort.user_cot.format(prefix="",
                                                    problem=sample.nat,
                                                    question=question)
            prompt_nat = substitute_objects(prompt_nat)
            return (PromptAndCheck(prompt=prompt_syn, answer=str(sample.label_syn["label"])),
                    PromptAndCheck(prompt=prompt_nat, answer=str(sample.label_syn["label"]))) # we keep the weight anyways

        case _:
            raise ValueError("Operation Type not supported")

def get_answer(prompt: str, model: str):
    @backoff.on_exception(backoff.expo, Exception, max_time=600)
    def query_engine(prompt: str):
        return utils.queryLLM(prompt, model)

    answer = query_engine(prompt)
    # print(answer)
    # now extract content in between the last occurrence of answer tags
    start = answer.rfind("<answer>")
    end = answer.rfind("</answer>")
    
    if start == -1 or end == -1:
        return "", answer

    return answer[start+8:end], answer

if __name__ == "__main__":
    main()


