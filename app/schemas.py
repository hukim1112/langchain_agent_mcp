import json
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
from dataclasses import dataclass, field

# 2. 에이전트 Context 및 State
# ==========================================
@dataclass
class SeniorCoderContext:
    pass
