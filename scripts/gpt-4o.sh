
for model in 'kim-schuster' 'parallel-paths' 'straight-line' 'nested-loop' 'sorting' # 'critical-path'
do
    python3 -m codesim.runner \
        --model gpt-4-azure  \
        --operation $operation --wandb
done

# python3 -m codesim.experiment --model gpt-4-azure --operation parallel-paths