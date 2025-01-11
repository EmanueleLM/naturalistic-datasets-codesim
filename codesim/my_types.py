
from pydantic import BaseModel
class Sample(BaseModel):
    syn: str
    nat: str
    label_syn: dict
    label_nat: dict