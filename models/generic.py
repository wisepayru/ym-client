from pydantic import BaseModel, Field
from typing import List, Optional

class GenericSuccessResponse(BaseModel):
    status: str

class ErrorDetail(BaseModel):
    code: str
    message: str

class GenericErrorResponse(BaseModel):
    status: str
    errors: Optional[List[ErrorDetail]] = Field(None)
