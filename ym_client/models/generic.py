from pydantic import BaseModel, Field
from typing import List, Optional

class GenericSuccessResponse(BaseModel):
    status: str

class ErrorDetail(BaseModel):
    code: str
    # optional in Market's ApiErrorDTO, where code alone is required
    message: Optional[str] = None

class GenericErrorResponse(BaseModel):
    status: Optional[str] = None
    errors: Optional[List[ErrorDetail]] = Field(None)
