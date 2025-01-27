
for model in 'kim-schuster' # 'straight-line' 'critical-path' 'parallel-paths' 'nested-loop' 'sorting' 'kim-schuster'
do
    python3 -m codesim.runner \
        --model sambanova-llama  \
        --operation $model --wandb
done


    # python3 -m codesim.experiment --model gpt-4-azurex  --operation kim-schuster --wandb