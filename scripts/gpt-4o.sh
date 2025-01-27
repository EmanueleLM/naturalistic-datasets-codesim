
for operation in 'straight-line' 'critical-path' 'parallel-paths' 'nested-loop' 'sorting' 'kim-schuster'
do
    python3 -m codesim.runner --model gpt-4o --operation $operation --wandb
done
