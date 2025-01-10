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

from pydantic import BaseModel, Field
import json
import argparse
import utils

class Sample(BaseModel):
    syn: str
    nat: str
    label_syn: dict =  Field(alias='label-syn')
    label_nat: dict =  Field(alias='label-nat')

def main():
    parser = argparse.ArgumentParser(description="Start experiments for the CodeSimulation project.")
    parser.add_argument('-o', '--operation', choices=['critical-path', 'parallel-paths', 'straight-line', 'nested-loop', 'sorting'], 
                        help='Type of operation to perform')
    parser.add_argument('-d', '--dataset_path', type=str, help='Path of the dataset')

    args = parser.parse_args()

    print(f"Operation: {args.operation}")
    print(f"Dataset Path: {args.dataset_path}")

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
    send_request(samples[0])


def send_request(sample: Sample):
    pretext = """You are given a text, what is the value of the last variable? Wrap your output into <answer> </answer> tags."""
    query_engine = lambda prompt: utils.queryLLM(prompt, './config.json', 'gpt-4o-mini')

    # Get the synthetic code
    syn_code = sample.syn
    query = pretext + syn_code

    answer = query_engine(query)
    print(answer)

if __name__ == "__main__":
    main()


