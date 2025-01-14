
from pydantic import BaseModel
from enum import Enum
class Sample(BaseModel):
    syn: str
    nat: str
    label_syn: dict
    label_nat: dict

# create enum class with the following possible types using pydantic 'kim-schuster', 'critical-path', 'parallel-paths', 'straight-line', 'nested-loop', 'sorting'], 

class OperationType(str, Enum):
    kim_schuster = 'kim-schuster'
    critical_path = 'critical-path'
    parallel_paths = 'parallel-paths'
    straight_line = 'straight-line'
    nested_loop = 'nested-loop'
    sorting = 'sorting'