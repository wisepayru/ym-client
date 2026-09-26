from datetime import date, datetime
from typing import Annotated, List, Optional

from pydantic import AwareDatetime, BaseModel, Field


class OrderDatesFilterDTO(BaseModel):
    creationDateFrom: Optional[date] = None
    creationDateTo: Optional[date] = None
    shipmentDateFrom: Optional[date] = None
    shipmentDateTo: Optional[date] = None
    # date-time on the method's page, which carries an offset
    updateDateFrom: Optional[AwareDatetime] = None
    updateDateTo: Optional[AwareDatetime] = None


class GetBusinessOrdersRequest(BaseModel):
    orderIds: Optional[List[int]] = Field(None, min_length=1, max_length=50)
    externalOrderIds: Optional[List[str]] = Field(None, min_length=1, max_length=50)
    programTypes: Optional[List[str]] = Field(None, min_length=1)
    campaignIds: Optional[List[Annotated[int, Field(ge=1)]]] = Field(None, min_length=1, max_length=50)
    statuses: Optional[List[str]] = Field(None, min_length=1)
    substatuses: Optional[List[str]] = Field(None, min_length=1)
    dates: Optional[OrderDatesFilterDTO] = None
    fake: Optional[bool] = None
    waitingForCancellationApprove: Optional[bool] = None
    sourcePlatforms: Optional[List[str]] = Field(None, min_length=1)


class CurrencyValueDTO(BaseModel):
    value: Optional[float] = None
    currencyId: Optional[str] = None


class ItemPriceDTO(BaseModel):
    payment: Optional[CurrencyValueDTO] = None
    subsidy: Optional[CurrencyValueDTO] = None
    cashback: Optional[CurrencyValueDTO] = None
    vat: Optional[str] = None


class OrderItemInstanceDTO(BaseModel):
    cis: Optional[str] = None
    cisFull: Optional[str] = None
    uin: Optional[str] = None
    rnpt: Optional[str] = None
    gtd: Optional[str] = None
    countryCode: Optional[str] = None


class OrderItemUnitStatusDTO(BaseModel):
    status: Optional[str] = None
    count: Optional[int] = None


class BusinessOrderItemDTO(BaseModel):
    id: Optional[int] = None
    offerId: Optional[str] = None
    offerName: Optional[str] = None
    count: Optional[int] = None
    prices: Optional[ItemPriceDTO] = None
    instances: Optional[List[OrderItemInstanceDTO]] = None
    requiredInstanceTypes: Optional[List[str]] = None
    itemStatuses: Optional[List[OrderItemUnitStatusDTO]] = None
    tags: Optional[List[str]] = None


class DeliveryPriceDTO(BaseModel):
    payment: Optional[CurrencyValueDTO] = None
    subsidy: Optional[CurrencyValueDTO] = None
    vat: Optional[str] = None


class OrderPriceDTO(BaseModel):
    payment: Optional[CurrencyValueDTO] = None
    subsidy: Optional[CurrencyValueDTO] = None
    cashback: Optional[CurrencyValueDTO] = None
    delivery: Optional[DeliveryPriceDTO] = None


class BusinessOrderDeliveryDatesDTO(BaseModel):
    fromDate: Optional[date] = None
    toDate: Optional[date] = None
    fromTime: Optional[str] = None
    toTime: Optional[str] = None
    realDeliveryDate: Optional[date] = None


class BusinessOrderShipmentDTO(BaseModel):
    id: Optional[int] = None
    shipmentDate: Optional[date] = None
    shipmentTime: Optional[str] = None


class GpsDTO(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class BusinessOrderDeliveryAddressDTO(BaseModel):
    country: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    subway: Optional[str] = None
    street: Optional[str] = None
    house: Optional[str] = None
    block: Optional[str] = None
    entrance: Optional[str] = None
    entryphone: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    gps: Optional[GpsDTO] = None


class RegionDTO(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    parent: Optional["RegionDTO"] = None


class BusinessOrderCourierDeliveryDTO(BaseModel):
    address: Optional[BusinessOrderDeliveryAddressDTO] = None
    region: Optional[RegionDTO] = None


class BusinessOrderPickupDeliveryDTO(BaseModel):
    address: Optional[BusinessOrderDeliveryAddressDTO] = None
    region: Optional[RegionDTO] = None
    logisticPointId: Optional[int] = None
    outletCode: Optional[str] = None
    outletStorageLimitDate: Optional[date] = None


class OrderCourierDTO(BaseModel):
    fullName: Optional[str] = None
    phone: Optional[str] = None
    phoneExtension: Optional[str] = None
    vehicleNumber: Optional[str] = None
    vehicleDescription: Optional[str] = None


class BusinessOrderEacDTO(BaseModel):
    eacType: Optional[str] = None
    eacCode: Optional[str] = None


class BusinessOrderTransferDTO(BaseModel):
    courier: Optional[OrderCourierDTO] = None
    eac: Optional[BusinessOrderEacDTO] = None


class BusinessOrderBoxLayoutPartialCountDTO(BaseModel):
    current: Optional[int] = None
    total: Optional[int] = None


class BriefOrderItemInstanceDTO(BaseModel):
    cis: Optional[str] = None
    uin: Optional[str] = None
    rnpt: Optional[str] = None
    gtd: Optional[str] = None
    countryCode: Optional[str] = None


class BusinessOrderBoxLayoutItemDTO(BaseModel):
    id: Optional[int] = None
    fullCount: Optional[int] = None
    partialCount: Optional[BusinessOrderBoxLayoutPartialCountDTO] = None
    instances: Optional[List[BriefOrderItemInstanceDTO]] = None


class BusinessOrderBoxLayoutDTO(BaseModel):
    items: Optional[List[BusinessOrderBoxLayoutItemDTO]] = None
    boxId: Optional[int] = None
    barcode: Optional[str] = None


class OrderTrackDTO(BaseModel):
    trackCode: Optional[str] = None
    deliveryServiceId: Optional[int] = None


class DigitalGoodsDeliveryDetailsDTO(BaseModel):
    type: Optional[str] = None
    steamLink: Optional[str] = None


class BusinessOrderDeliveryDTO(BaseModel):
    type: Optional[str] = None
    serviceName: Optional[str] = None
    deliveryServiceId: Optional[int] = None
    warehouseId: Optional[str] = None
    deliveryPartnerType: Optional[str] = None
    dispatchType: Optional[str] = None
    dates: Optional[BusinessOrderDeliveryDatesDTO] = None
    shipment: Optional[BusinessOrderShipmentDTO] = None
    courier: Optional[BusinessOrderCourierDeliveryDTO] = None
    pickup: Optional[BusinessOrderPickupDeliveryDTO] = None
    transfer: Optional[BusinessOrderTransferDTO] = None
    boxesLayout: Optional[List[BusinessOrderBoxLayoutDTO]] = None
    tracks: Optional[List[OrderTrackDTO]] = None
    estimated: Optional[bool] = None
    receiveBarcode: Optional[str] = None
    receiveCode: Optional[str] = None
    digitalGoods: Optional[DigitalGoodsDeliveryDetailsDTO] = None


class BusinessOrderServicesDTO(BaseModel):
    liftType: Optional[str] = None


class BusinessOrderDTO(BaseModel):
    orderId: Optional[int] = None
    campaignId: Optional[int] = None
    programType: Optional[str] = None
    externalOrderId: Optional[str] = None
    status: Optional[str] = None
    substatus: Optional[str] = None
    # ISO 8601 with a UTC offset, so these parse timezone-aware, unlike getOrder's
    # offset-less Moscow-time strings
    creationDate: Optional[datetime] = None
    updateDate: Optional[datetime] = None
    paymentType: Optional[str] = None
    paymentMethod: Optional[str] = None
    fake: Optional[bool] = None
    items: Optional[List[BusinessOrderItemDTO]] = None
    prices: Optional[OrderPriceDTO] = None
    delivery: Optional[BusinessOrderDeliveryDTO] = None
    services: Optional[BusinessOrderServicesDTO] = None
    buyerType: Optional[str] = None
    notes: Optional[str] = None
    cancelRequested: Optional[bool] = None
    sourcePlatform: Optional[str] = None


class PackagingForwardScrollingPagerDTO(BaseModel):
    nextPageToken: Optional[str] = None


class BusinessOrdersResponse(BaseModel):
    orders: List[BusinessOrderDTO]
    paging: Optional[PackagingForwardScrollingPagerDTO] = None
