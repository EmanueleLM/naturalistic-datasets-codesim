### Replicate the experiments in the paper.
To replicate the experiments of the paper, first install all the requirements.
I will assume you have Python3 (any version should be fine, for sure 3.10 works well) and pip/pip3.
Then run:
```pip3 install -r requirements.txt```

Next, you should add the environment variables to call an API model.
We suggest to add a `config.py` file inside the `./codesim` folder with the following format.
Please notice this is meant to work with GPT-4 and GPT-4o hosted by Microsoft Azure, while Llama is hosted by Sambanova.

```
config = {
        "gpt-4-azure": {
            "name": "name-of-the-model",
            "api_type": "azure",
            "api_base": "the API call base",
            "api_version": "API version",
            "key": "your key"
        },
        "gpt-4o": {
            "name": "gpt-4o",
            "api_type": "azure",
            "api_base": "the API call base",
            "api_version": "API version",
            "key": "your key"
        },
        "sambanova-llama": {
            "organization": "local",
            "name":"Meta-Llama-3.1-405B-Instruct",
            "key":"your key"
        }
}
```

Next, you can run all the experiments by simply opening a terminal:
```sh ./script/<MODEL>.sh```
Where <MODEL> is either 'gpt-4', 'gpt-4o', or 'llama'. We suggest to use tmux or screen to handle each session.

### Inspect the logs
Unzip the `logs.zip` file. The uncompressed size is around ~250BM.

### Data Generation.
The data is sampled from `./data`. If you want to generate different samples, please check `generate_data.ipynb`.
There is no need to generate new data, the code already comes with randomly generated data and some backup.

### Inspect the prompts
Run `prompts.ipynb` to check some prompts used in the experiments.

### Generating the plots
Simply run `plot.ipynb` to replicate all the results in the paper.