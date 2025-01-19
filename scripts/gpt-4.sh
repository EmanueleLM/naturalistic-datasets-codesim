
for operation in 'kim-schuster'  'parallel-paths' 'straight-line' 'nested-loop' 'sorting' # 'critical-path'
do
    # python3 -m codesim.experiment \
    #     --model gpt-4-azure  \
    #     --operation $model --wandb
    python3 -m codesim.runner \
        --model gpt-4-azure  \
        --operation $operation --wandb
done
