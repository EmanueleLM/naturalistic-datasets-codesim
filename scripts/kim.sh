
for model in 'kim-schuster'  'parallel-paths' 'straight-line' 'nested-loop' 'sorting' # 'critical-path'
do
    python3 -m codesim.experiment \
        --model sambanova-llama  \
        --operation $model --wandb
done


    # python3 -m codesim.experiment --model gpt-4-azurex  --operation kim-schuster --wandb