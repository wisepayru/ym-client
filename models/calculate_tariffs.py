from typing import List, Optional
from pydantic import BaseModel


class TariffParameterDTO(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class TariffDTO(BaseModel):
    type: str
    amount: float
    currency: str
    parameters: Optional[List[TariffParameterDTO]] = None


class TariffOfferDTO(BaseModel):
    categoryId: Optional[int] = None
    price: Optional[float] = None
    weight: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    quantity: Optional[int] = None


class CalculatedOfferDTO(BaseModel):
    offer: TariffOfferDTO
    tariffs: List[TariffDTO]


class CalculateTariffsResult(BaseModel):
    offers: List[CalculatedOfferDTO]


class CalculateTariffsResponse(BaseModel):
    status: str
    result: CalculateTariffsResult
