import json
import openai
import tiktoken
import requests
import os
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import backoff
import transformers
# from groq import Groq
from functools import partial
import numpy as np
from openai import AzureOpenAI  


__encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")

# We assume that on a single process at most a single model is loaded.
local_model = None
local_tokenizer = None

local_model = None
local_tokenizer = None

total_cost = 0

def get_total_cost():
    return total_cost

class OverloadedException(Exception):
    pass
def _query_model_handle_errors(prompts: list[str],
                                config_file: str,
                                model_name: str,
                                encoder: tiktoken.Encoding = None,
                                max_tokens: int = 15000,
                                tag: str = "#GPT#",
                                **kwargs
) -> list[str]:
    assert len(prompts) > 0, "The number of prompts should be greater than 0"
    global local_model, local_tokenizer

    batched = len(prompts) > 1
    prompt = prompts[0]  # for legacy compatibility

    if model_name.startswith("gpt"):
        # Currently this method is just a quick way to make it seem batched outside
        description = [""] * len(prompts)
        for i, prompt in enumerate(prompts):

            @backoff.on_exception(backoff.expo, Exception, max_time=180)
            def backoffQueryLLM(prompt, **kwargs):
                return queryLLM(prompt, config_file, model_name, **kwargs)
            
            description[i] = backoffQueryLLM(prompt, **kwargs)
    elif model_name.startswith("other"):  # assume it is a local model
        if batched:
            raise ValueError("Batched queries are not supported for this")
        import json
        with open(config_file, "r") as f:
            config_json = json.load(f)

        name = config_json[model_name]["name"]
        if local_model is None:
            local_model = AutoModelForCausalLM.from_pretrained(name, device_map="auto", cache_dir=".cache/huggingface/hub")
            local_tokenizer = AutoTokenizer.from_pretrained(name, cache_dir=".cache/huggingface/hub")
            local_model.eval()

        try:
            device = local_model.device
            inputs = local_tokenizer(prompt, return_tensors="pt").to(device)
            description = local_model.generate(**inputs, max_length=512, num_return_sequences=1, do_sample=False)
            description = local_tokenizer.decode(description[0], skip_special_tokens=True)
        except Exception as e:
            print(e)
            description = "<No answer>"
    else:

        @backoff.on_exception(backoff.expo, OverloadedException, max_time=7200)
        def backoffQueryLLM(prompt, config_file, model_name, **kwargs):
            return queryLLM(prompt, config_file, model_name, **kwargs)
        description = [""] * len(prompts)
        for i, prompt in enumerate(prompts):
            description[i] = backoffQueryLLM(prompt, './config.json', model_name, max_new_tokens=2048, **kwargs)

    return description

def queryLLM(prompt, model, **kwargs):
    from . import config
    global f_query

    jdata = config.config
    response = None
    try:
        # print(f"Querying {model}. Available models: {[m for m in f_query.keys()]}.")
        # print()
        response = f_query[model](prompt, jdata[model], **kwargs)
    except Exception as inst:
        # print exception info
        print(type(inst))    # the exception instance
        print(f"[error] Querying model {model} has failed. Error: {inst}")
        raise inst

    return response

# def queryllama2(prompt, jdata):
#     client = InferenceClient(model="meta-llama/Llama-2-70b-chat-hf", token=jdata['key'])
#     completion = client.text_generation(prompt, 
#                                         max_new_tokens=2000,
#                                         temperature=0.7)
    return completion

def queryllama(prompt, jdata, max_new_tokens=500, device="cpu"):
    """_summary_

    Args:
        prompt (str): input prompt
        jdata (dict): config file
        llm (class): Huggingface LLM model
        tokenizer (class): Huggingface tokenizer

    Returns:
        str: output string after model inference
    """
    global local_model, local_tokenizer
    model_name = jdata['name']  
    
    match model_name:
        case "llama-13B":
            llama_path = "./.cache/llama-13b-chat"
        case "llama-3-8B":
            llama_path = "meta-llama/Meta-Llama-3-8B-Instruct"
        case _:
            raise ValueError(f"Model {model_name} not supported")
        
    if local_model is None:
        local_model = transformers.pipeline(
            "text-generation",
            model=llama_path,
            device_map=device,
        )
    llm = local_model

    device = llm.device

    messages = [
        {"role": "user", "content": prompt},
    ]

    prompt = local_model.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
    )

    terminators = [
        local_model.tokenizer.eos_token_id,
        local_model.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    completion = local_model(
        prompt,
        max_new_tokens=max_new_tokens,
        eos_token_id=terminators,
        do_sample=False,
    )
    # OLD CODE don't use this
    # model_inputs = tokenizer.apply_chat_template(chat, tokenize=True, return_dict=True, add_generation_prompt=True, return_tensors="pt").to(device)
    # model_inputs = tokenizer([prompt], return_tensors="pt").to(device)
    # out = llm.generate(**model_inputs, max_new_tokens=max_new_tokens, pad_token_id=tokenizer.eos_token_id, do_sample=False)
    # completion = tokenizer.decode(out[0])
    # prefix = tokenizer.decode(model_inputs["input_ids"][0])
    print(completion[0]["generated_text"][len(prompt):])
    return completion[0]["generated_text"][len(prompt):]


def queryllamachat(messages, jdata, max_new_tokens=500, device="cpu"):
    """_summary_

    Args:
        prompt (str): input prompt
        jdata (dict): config file
        llm (class): Huggingface LLM model
        tokenizer (class): Huggingface tokenizer

    Returns:
        str: output string after model inference
    """
    global local_model, local_tokenizer
    model_name = jdata['name']  
    
    match model_name:
        case "llama-3-8B-chat":
            llama_path = "meta-llama/Meta-Llama-3-8B-Instruct"
        case _:
            raise ValueError(f"Model {model_name} not supported")
        
    if local_model is None:
        local_model = transformers.pipeline(
            "text-generation",
            model=llama_path,
            device_map=device,
        )
    llm = local_model

    device = llm.device

    prompt = local_model.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
    )

    terminators = [
        local_model.tokenizer.eos_token_id,
        local_model.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    completion = local_model(
        prompt,
        max_new_tokens=max_new_tokens,
        eos_token_id=terminators,
        do_sample=False,
    )

    return completion[0]["generated_text"][len(prompt):]

def querygemma(prompts: list[str], jdata, max_new_tokens=500, device="cuda:3"):
    """
    Args:
        prompt (list): list of batched inputs
        jdata (dict): config file
        llm (class): Huggingface LLM model
        tokenizer (class): Huggingface tokenizer
    """
    global local_model, local_tokenizer

    model_name = os.path.join(jdata["organization"], jdata['name'])
    cache_dir = "./.cache/huggingface/hub"
    if local_model is None:
        local_tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        local_model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=device,
            cache_dir=cache_dir,
        )
    llm = local_model
    tokenizer = local_tokenizer

    device = llm.device
    chats = ["" for _ in range(len(prompts))]
    for i, p in enumerate(prompts):
        role_dict = [{"role": "user", "content": p}]
        chats[i] = tokenizer.apply_chat_template(role_dict, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer(chats, add_special_tokens=False, padding=True, return_tensors="pt").to(device)
    out = llm.generate(**model_inputs, max_new_tokens=max_new_tokens, pad_token_id=tokenizer.eos_token_id, temperature=0)

    output = ["" for _ in range(len(prompts))]
    for i, o in enumerate(out):
        completion = tokenizer.decode(o)
        prefix = chats[i]
        output[i] = completion[len(prefix):]

    return output

def querygpt(prompt, jdata):
    """
    https://platform.openai.com/docs/guides/gpt/chat-completions-api
    """

    model_name = jdata['name']
    
    if "api_base" in jdata:
        client = openai.Client(api_key=jdata['key'], base_url=jdata['api_base'])
    else:
        client = openai.Client(api_key=jdata['key'])

    completion = client.chat.completions.create(
                                                model = model_name,
                                                messages = [
                                                    {'role': 'user', 'content': f'{prompt}'}
                                                ],
                                                temperature = 0.,
                                                )
    return completion.choices[0].message.content

def queryllamasambanova(prompt, jdata):
    
    model_name = jdata['name']
    api_key = jdata['key']

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.sambanova.ai/v1",
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role":"system","content":"You are a helpful assistant"},{"role":"user","content":prompt}],
            temperature =  0.1,
            top_p = 0.1
        )
    except Exception as e:
        raise e

    return response.choices[0].message.content

class CostClass(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    cumulative_tokens: int
    cumulative_cost: float

def track_costs(model_name: str, completion, input_cost: float, output_cost: float):
    global total_cost
    try:
        example_cost = CostClass(prompt_tokens=0, completion_tokens=0, cumulative_tokens=0, cumulative_cost=0)
        global __encoder
        update_cost_path = f"./costs/costs-{model_name}.txt"
        os.makedirs(os.path.dirname(update_cost_path), exist_ok=True)
        if not os.path.exists(update_cost_path):
            with open(update_cost_path, 'w') as f:
                f.write(example_cost.model_dump_json(indent=2))
                pass

        prompt_tokens = completion.usage["prompt_tokens"]
        completion_tokens = completion.usage["completion_tokens"]

        with open(update_cost_path, "r") as f:
            json_data = json.load(f)
            example_cost = CostClass(**json_data)

        with open(update_cost_path, "w") as f:
            example_cost.prompt_tokens += prompt_tokens
            example_cost.completion_tokens += completion_tokens
            example_cost.cumulative_tokens += prompt_tokens + completion_tokens
            example_cost.cumulative_cost = (example_cost.prompt_tokens * input_cost + example_cost.completion_tokens * output_cost)/1000
            f.write(example_cost.model_dump_json(indent=2))

        total_cost += (prompt_tokens * input_cost + completion_tokens * output_cost) / 1000
    except Exception as e:
        print(e) # if it doesn't update, that's fine
    
def queryinstruct(prompt, jdata):
    """
    https://platform.openai.com/docs/guides/gpt/chat-completions-api
    """
    openai.organization = jdata['organization']
    openai.api_key = jdata['key']
    model_name = jdata['name']

    completion = openai.Completion.create(
        model=model_name, 
        prompt=prompt,
        max_tokens=30,
        temperature=0.,
        logprobs=5,
        frequency_penalty=0,
        presence_penalty=0,
        echo=False
    )
    track_costs(model_name, completion, 0.0015, 0.002)

    return completion

def querygptazurechat(prompt, jdata):
    openai.api_type = jdata['api_type']
    openai.base_url = jdata['api_base']
    openai.api_version = jdata['api_version']
    openai.api_key = jdata['key']
    model_name = jdata['name']

    try:
        completion = openai.chat.completions.create(
            model=model_name,
            messages = prompt,
            temperature=0.,
            # max_tokens=1000,
            max_tokens=1000,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )
    except openai.APIError as e:
        print(e)
        print("Azure filtered this request: ", prompt)
        # return "error"
        raise e
    
    track_costs(model_name+"chat", completion, 0.0015, 0.002) # This should be upper bound cost

    try:
        completion = completion['choices'][0]['message']['content']
    except KeyError as e:
        print("Completion filtered by Azure")
        # completion = "error"
        raise e
    return completion

def querygptazure(prompt, jdata, temperature=0., n=1, stop=None):
    """
    GPT-4 Azure endpoint required (stored locally)
    """
    client = AzureOpenAI(  
        azure_endpoint=jdata['api_base'],  
        api_key=jdata['key'],  
        api_version="2024-05-01-preview",
    )
    model_name = jdata['name']

    # message_text = [{"role":"system","content":"You are an AI assistant that helps people find information."}, \
    #                 {"role":"user","content": prompt}]

    message_text = [{"role":"user","content": prompt}]

    outputs = []
    try: 
        completion = client.chat.completions.create(
                                                    model=model_name,
                                                    messages = message_text,
                                                    temperature=temperature,
                                                    max_tokens=1000,
                                                    frequency_penalty=0,
                                                    presence_penalty=0,
                                                    stop=stop,
                                                    n=n
        )
    except openai.APIError as e:
        print(e)
        print("content filtered")
        raise e
        # for i in range(n):
        #     outputs.append("error")
        # return outputs

    for completion in completion.choices:
        try:
            outputs.append(completion.message.content)
        except KeyError as e:
            print("Completion filtered by Azure")
            # outputs.append("error")
            raise e
    # outputs.extend([choice["message"]["content"] for choice in completion["choices"]])

    # track_costs(model_name+"-new", completion, 0.0015, 0.002) # This should be upper bound cost
    if len(outputs) == 1:  # backwards compatibility
        return outputs[0]
    else:
        return outputs

f_query = {
    'gpt-3.5':querygpt, 
    'gpt-4o-mini': querygpt,
    'gpt-3.5-azure':querygptazure,
    'gpt-3.5-azure-chat': querygptazurechat,
    'gpt-4':querygpt, 
    'gpt-4o': querygptazure,
    'gpt-4-azure': querygptazure,
    'gpt-4-azure-chat': querygptazurechat,
    # 'llama2-70B':queryllama2,
    'llama-13B':queryllama,
    'llama-3-8B':queryllama,
    'llama-3-8B-chat':queryllamachat,
    'gemma-2B':querygemma,
    'gemma-7B':querygemma,
    'gpt-3.5-instruct': queryinstruct,
    'sambanova-llama': queryllamasambanova
}