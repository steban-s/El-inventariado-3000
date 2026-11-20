from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from core.database import obtener_bd
from models.factura import Factura as FacturaModel
from models.orden import Orden as OrdenModel
from models.orden_repuesto import OrdenRepuesto as OrdenRepuestoModel
from schemas.factura import FacturaDetalladaResponse, MotoInfo, RepuestoCobrado

router = APIRouter(prefix="/facturas", tags=["Facturación"])


@router.get("/{orden_id}", response_model=FacturaDetalladaResponse)
async def obtener_factura(orden_id: int, db: AsyncSession = Depends(obtener_bd)):
    sentencia = (
        select(FacturaModel)
        .where(FacturaModel.orden_id == orden_id)
        .options(
            joinedload(FacturaModel.orden).joinedload(OrdenModel.mecanico),
            joinedload(FacturaModel.orden)
            .selectinload(OrdenModel.repuestos_usados)
            .joinedload(OrdenRepuestoModel.repuesto),
        )
    )
    resultado = await db.execute(sentencia)
    factura = resultado.scalar_one_or_none()

    if not factura:
        raise HTTPException(status_code=404, detail="La orden no tiene factura")

    orden = factura.orden

    lineas = [
        RepuestoCobrado(
            nombre_repuesto=r.repuesto.nombre,
            cantidad=r.cantidad,
            precio_unitario_historico=r.precio_unitario_historico,
            subtotal_linea=r.cantidad * r.precio_unitario_historico,
        )
        for r in orden.repuestos_usados
    ]

    return FacturaDetalladaResponse(
        id=factura.id,
        fecha_emision=factura.fecha_emision,
        subtotal_repuestos=factura.subtotal_repuestos,
        costo_mano_obra=factura.costo_mano_obra,
        iva=factura.iva,
        total_pagar=factura.total_pagar,
        moto=MotoInfo(placa=orden.placa, modelo=orden.modelo),
        mecanico=orden.mecanico.nombre_completo if orden.mecanico else None,
        repuestos=lineas,
    )