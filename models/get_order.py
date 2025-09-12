from typing import Optional, List
from pydantic import BaseModel

class Promo(BaseModel):
    type: Optional[str] = None
    discount: Optional[float] = None
    subsidy: Optional[float] = None
    shopPromoId: Optional[str] = None
    marketPromoId: Optional[str] = None

class Instance(BaseModel):
    cis: Optional[str] = None
    cisFull: Optional[str] = None
    uin: Optional[str] = None
    rnpt: Optional[str] = None
    gtd: Optional[str] = None
    countryCode: Optional[str] = None

class ItemDetail(BaseModel):
    itemCount: Optional[int] = None
    itemStatus: Optional[str] = None
    updateDate: Optional[str] = None

class Subsidy(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = None

class Item(BaseModel):
    id: Optional[int] = None
    offerId: Optional[str] = None
    offerName: Optional[str] = None
    price: Optional[float] = None
    buyerPrice: Optional[float] = None
    buyerPriceBeforeDiscount: Optional[float] = None
    priceBeforeDiscount: Optional[float] = None
    count: Optional[int] = None
    vat: Optional[str] = None
    shopSku: Optional[str] = None
    subsidy: Optional[float] = None
    partnerWarehouseId: Optional[str] = None
    promos: Optional[List[Promo]] = None
    instances: Optional[List[Instance]] = None
    details: Optional[List[ItemDetail]] = None
    subsidies: Optional[List[Subsidy]] = None
    requiredInstanceTypes: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class GPS(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Address(BaseModel):
    country: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    subway: Optional[str] = None
    street: Optional[str] = None
    house: Optional[str] = None
    estate: Optional[str] = None
    block: Optional[str] = None
    building: Optional[str] = None
    entrance: Optional[str] = None
    entryphone: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    phone: Optional[str] = None
    recipient: Optional[str] = None
    gps: Optional[GPS] = None

class Region(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None

class Courier(BaseModel):
    fullName: Optional[str] = None
    phone: Optional[str] = None
    phoneExtension: Optional[str] = None
    vehicleNumber: Optional[str] = None
    vehicleDescription: Optional[str] = None

class Dates(BaseModel):
    fromDate: Optional[str] = None
    toDate: Optional[str] = None
    fromTime: Optional[str] = None
    toTime: Optional[str] = None
    realDeliveryDate: Optional[str] = None

class Track(BaseModel):
    trackCode: Optional[str] = None
    deliveryServiceId: Optional[int] = None

class Box(BaseModel):
    id: Optional[int] = None
    fulfilmentId: Optional[str] = None

class Shipment(BaseModel):
    id: Optional[int] = None
    shipmentDate: Optional[str] = None
    shipmentTime: Optional[str] = None
    tracks: Optional[List[Track]] = None
    boxes: Optional[List[Box]] = None

class Delivery(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    serviceName: Optional[str] = None
    price: Optional[float] = None
    deliveryPartnerType: Optional[str] = None
    courier: Optional[Courier] = None
    dates: Optional[Dates] = None
    region: Optional[Region] = None
    address: Optional[Address] = None
    vat: Optional[str] = None
    deliveryServiceId: Optional[int] = None
    liftType: Optional[str] = None
    liftPrice: Optional[float] = None
    outletCode: Optional[str] = None
    outletStorageLimitDate: Optional[str] = None
    dispatchType: Optional[str] = None
    tracks: Optional[List[Track]] = None
    shipments: Optional[List[Shipment]] = None
    estimated: Optional[bool] = None
    eacType: Optional[str] = None
    eacCode: Optional[str] = None

class Buyer(BaseModel):
    id: Optional[str] = None
    lastName: Optional[str] = None
    firstName: Optional[str] = None
    middleName: Optional[str] = None
    type: Optional[str] = None

class Order(BaseModel):
    id: Optional[int] = None
    externalOrderId: Optional[str] = None
    status: Optional[str] = None
    substatus: Optional[str] = None
    creationDate: Optional[str] = None
    updatedAt: Optional[str] = None
    currency: Optional[str] = None
    itemsTotal: Optional[float] = None
    deliveryTotal: Optional[float] = None
    buyerItemsTotal: Optional[float] = None
    buyerTotal: Optional[float] = None
    buyerItemsTotalBeforeDiscount: Optional[float] = None
    buyerTotalBeforeDiscount: Optional[float] = None
    paymentType: Optional[str] = None
    paymentMethod: Optional[str] = None
    fake: Optional[bool] = None
    items: Optional[List[Item]] = None
    subsidies: Optional[List[Subsidy]] = None
    delivery: Optional[Delivery] = None
    buyer: Optional[Buyer] = None
    notes: Optional[str] = None
    taxSystem: Optional[str] = None
    cancelRequested: Optional[bool] = None
    expiryDate: Optional[str] = None

class OrderResponse(BaseModel):
    order: Optional[Order] = None
