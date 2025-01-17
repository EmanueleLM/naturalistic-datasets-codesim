
for model in 'kim-schuster' 'critical-path' 'parallel-paths' 'straight-line' 'nested-loop' 'sorting'
do
    python3 -m codesim.experiment \
        --model gpt-4-azurex  \
        --operation $model --wandb
done
