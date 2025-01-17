
for model in 'kim-schuster' 'critical-path' 'parallel-paths' 'straight-line' 'nested-loop' 'sorting'
do
    python3 -m codesim.experiment \
        --model sambanova-llama  \
        --operation $model --wandb
done


    # python3 -m codesim.experiment --model gpt-4-azurex  --operation kim-schuster --wandb