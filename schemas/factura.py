from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MotoInfo(BaseModel):
    placa: str
    modelo: Optional[str] = None


class RepuestoCobrado(BaseModel):
    nombre_repuesto: str
    cantidad: int
    precio_unitario_historico: float
    subtotal_linea: float


class FacturaDetalladaResponse(BaseModel):
    id: int
    fecha_emision: datetime
    subtotal_repuestos: float
    costo_mano_obra: float
    iva: float
    total_pagar: float
    moto: MotoInfo
    mecanico: Optional[str] = None
    repuestos: List[RepuestoCobrado]