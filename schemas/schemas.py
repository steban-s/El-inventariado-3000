from pydantic import BaseModel, Field, model_validator
from typing import Optional

class OrdenCreate(BaseModel):
    placa: str = Field(..., min_length=5, max_length=6, description="Placa de la moto (sin espacios)")
    modelo: str = Field(..., description="Marca y modelo. Ej: Bajaj Dominar 400")
    falla_reportada: str = Field(..., description="Descripción del problema por el cliente")


class OrdenUpdate(BaseModel):
    nuevo_estado: str = Field(..., description="Ej: En diagnóstico, Reparada, Entregada")
    costo_reparacion: float = Field(..., ge=0, description="Debe ser 0 o mayor")

    @model_validator(mode='after')
    def validar_costo_reparacion(self):
        if self.nuevo_estado == "Reparada" and self.costo_reparacion == 0:
            raise ValueError("No se puede marcar como reparada sin asignar un costo de reparación mayor a cero.")

        self.nuevo_estado = self.nuevo_estado.capitalize()
        return self


class OrdenPatch(BaseModel):
    nuevo_estado: Optional[str] = Field(None, description="Ej: En diagnóstico, Reparada, Entregada")
    costo_reparacion: Optional[float] = Field(None, ge=0)
    falla_reportada: Optional[str] = None


class OrdenResponse(BaseModel):
    id: int
    estado: str
    costo_reparacion: float

    model_config = {"from_attributes": True}

class MecanicoCreate(BaseModel):
    documento: str = Field(..., max_length=15)
    nombre_completo: str = Field(..., max_length=100)
    especialidad: str = Field(..., max_length=50)


class MecanicoResponse(MecanicoCreate):
    id: int
    activo: bool = True

    model_config = {"from_attributes": True}

class RepuestoCreate(BaseModel):
    codigo_sku: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    precio_compra: float = Field(..., ge=0)
    precio_venta: float = Field(..., ge=0)
    stock_actual: int = Field(0, ge=0)


class RepuestoResponse(RepuestoCreate):
    id: int

    model_config = {"from_attributes": True}