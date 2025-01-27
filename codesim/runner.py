"""
This file's responsibility is to restart the experiments when they are not running fine.
"""

import argparse
import os
import datetime
from time import sleep
import pandas as pd

from .my_types import Sample, OperationType
from .experiment import get_dataset_path

def main():
    parser = argparse.ArgumentParser(description="Start experiments for the CodeSimulation project.")
    parser.add_argument('-o', '--operation', choices=['kim-schuster', 'critical-path', 'parallel-paths', 'straight-line', 'nested-loop', 'sorting'], 
                        help='Type of operation to perform')
    parser.add_argument('-m', '--model', type=str, help='Model to use for the experiment')
    parser.add_argument('--wandb', action='store_true', help='Use wandb for logging, if not, use default txt file')

    
    args = parser.parse_args()
    op_type: OperationType = OperationType(args.operation)
    dataset_base = get_dataset_path(op_type)
    dataset_list = []
    for dataset in os.listdir(dataset_base):
        dataset_list.append(os.path.join(dataset_base, dataset))
    dataset_list = sorted(dataset_list)
    
    for dataset in dataset_list:
        dataset_name = os.path.basename(dataset)
        if check_results(args, dataset_name):
            print(f"Skipping {dataset_name}...")
            continue

        print(f"Running {dataset_name}...")
        i = 0
        while i < 1:
            os.system(f"python3 -m codesim.experiment -o {args.operation} -m {args.model} --dataset_path {dataset} {'--wandb' if args.wandb else ''}")
            if check_results(args, dataset_name):
                break
            # allow to kill the main program
            sleep(2)
            i += 1
            print(f"Failed to run {dataset_name}... Trying again...")
        else:
            print(f"Failed to run {dataset_name}... Going next")
        print(f"Finished {dataset_name}...")

def check_results(args, dataset_name):
    basedir = os.path.join("results", args.operation)
    os.makedirs(basedir, exist_ok=True)
    
    filename = f"{basedir}/{args.model}.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        
        # check if dataset_name is already in the dataframe
        if dataset_name in df["dataset"].values:
            return True

    return False

if __name__ == "__main__":
    # test if works
    main()