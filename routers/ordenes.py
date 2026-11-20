from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.database import obtener_bd
from models.orden import Orden as OrdenModel
from models.mecanico import Mecanico as MecanicoModel
from models.repuesto import Repuesto as RepuestoModel
from models.orden_repuesto import OrdenRepuesto as OrdenRepuestoModel
from models.factura import Factura as FacturaModel
from typing import Optional, List
from schemas.ordenes import OrdenCreate, OrdenPatch, OrdenResponse, AgregarRepuestoOrden, RepuestoEnOrdenResponse
from dependencias import verificar_api_key, parametros_paginacion
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/ordenes", tags=["Gestionar ordenes"])

TASA_IVA = 0.19

@router.get("/", response_model=List[OrdenResponse])
async def obtener_ordenes(
    estado: Optional[str] = None,
    paginacion: dict = Depends(parametros_paginacion), 
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).options(joinedload(OrdenModel.mecanico))
    resultado = await db.execute(sentencia)
    ordenes = resultado.scalars().all() # Traer los objetos (No "lenguaje" sql)

    return ordenes

@router.get("/{orden_id}", response_model=OrdenResponse)
async def obtener_orden_por_id(
    orden_id: int,
    db: AsyncSession = Depends(obtener_bd)
):
    # SELECT * FROM ordenes WHERE id = orden_id
    sentencia = select(OrdenModel).options(joinedload(OrdenModel.mecanico)).where(OrdenModel.id == orden_id)
    resultado = await db.execute(sentencia)

    orden = resultado.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    return orden

@router.post("/", status_code=201)
async def crear_orden(
    orden: OrdenCreate,
    api_key: str = Depends(verificar_api_key), 
    db: AsyncSession = Depends(obtener_bd)
):

    consulta_mec = select(MecanicoModel).where(MecanicoModel.id == orden.mecanico_id)
    res_mec = await db.execute(consulta_mec)
    mecanico_db = res_mec.scalar_one_or_none()

    if not mecanico_db or not mecanico_db.activo:
        raise HTTPException(
            status_code=400,
            detail=f"El mecanico con el ID {orden.mecanico_id} no existe o está inactivo."  # (antes decía "datail")
        )
    
    nueva_orden = OrdenModel(**orden.model_dump())

    db.add(nueva_orden)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al guardar la base de datos")

    await db.refresh(nueva_orden)

    return {"mensaje": "Orden creada", "orden": nueva_orden}

@router.delete("/{placa}", status_code=204)
async def eliminar_orden(
    placa: str,
    db: AsyncSession = Depends(obtener_bd)
):
    sentencia = select(OrdenModel).where(OrdenModel.placa == placa)
    resultado = await db.execute(sentencia)
    orden = resultado.scalar_one_or_none()

    if not orden:
        raise HTTPException(status_code=404, detail="La orden no existe")

    await db.delete(orden)
    await db.commit()
    return None

@router.patch("/{orden_id}")
async def actualizacion_parcial(
    orden_id: int,
    orden_patch: OrdenPatch,
    db: AsyncSession = Depends(obtener_bd)
):
    # SELECT * FROM ordenes WHERE id == orden_id
    sentencia = select(OrdenModel).where(OrdenModel.id == orden_id)
    resultado = await db.execute(sentencia)
    orden = resultado.scalar_one_or_none()

    if not orden:
        raise HTTPException(status_code=404, detail="La orden no existe")

    datos_a_actualizar = orden_patch.model_dump(exclude_unset=True)
    mano_obra = datos_a_actualizar.pop("mano_obra", None)

    if "nuevo_estado" in datos_a_actualizar:
        datos_a_actualizar["estado"] = datos_a_actualizar.pop("nuevo_estado")

    nueva_factura = None

    if datos_a_actualizar.get("estado") == "Reparada":
        res_fac = await db.execute(
            select(FacturaModel).where(FacturaModel.orden_id == orden.id)
        )
        factura_existente = res_fac.scalar_one_or_none()

        if factura_existente is None:
            res_rep = await db.execute(
                select(OrdenRepuestoModel).where(OrdenRepuestoModel.orden_id == orden.id)
            )
            repuestos = res_rep.scalars().all()

            subtotal_repuestos = sum(
                r.cantidad * r.precio_unitario_historico for r in repuestos
            )
        
            costo_base = datos_a_actualizar.get("costo_reparacion", orden.costo_reparacion) or 0.0
            costo_total = costo_base + (mano_obra or 0.0)

            if costo_total <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="No se puede marcar como Reparada ni facturar una orden con costo de reparación 0."
                )

            costo_mano_obra = costo_total - subtotal_repuestos
            total_neto = subtotal_repuestos + costo_mano_obra
            iva = total_neto * TASA_IVA
            total_pagar = total_neto + iva

            datos_a_actualizar["costo_reparacion"] = costo_total

            nueva_factura = FacturaModel(
                orden_id=orden.id,
                subtotal_repuestos=round(subtotal_repuestos, 2),
                costo_mano_obra=round(costo_mano_obra, 2),
                iva=round(iva, 2),
                total_pagar=round(total_pagar, 2),
            )
            db.add(nueva_factura)

    for campo, valor in datos_a_actualizar.items():
        setattr(orden, campo, valor)

    try:
        await db.commit()
        await db.refresh(orden)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error aplicando la actualización parcial.")

    return {"mensaje": "La orden ha sido actualizada con éxito", "orden": orden}

@router.post("/{orden_id}/repuestos", status_code=201, response_model=RepuestoEnOrdenResponse)
async def agregar_repuesto_a_orden(
    orden_id: int,
    datos: AgregarRepuestoOrden,
    db: AsyncSession = Depends(obtener_bd)
):
    # 1. Validar que la orden exista
    res_orden = await db.execute(select(OrdenModel).where(OrdenModel.id == orden_id))
    orden_db = res_orden.scalar_one_or_none()
    if not orden_db:
        raise HTTPException(status_code=404, detail="La orden de servicio no existe")

    res_fac = await db.execute(select(FacturaModel).where(FacturaModel.orden_id == orden_id))
    if orden_db.estado == "Reparada" or res_fac.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=400,
            detail="No se pueden modificar repuestos de una orden ya cerrada/facturada"
        )

    # 2. Validar que el repuesto exista
    res_rep = await db.execute(select(RepuestoModel).where(RepuestoModel.id == datos.repuesto_id))
    rep_db = res_rep.scalar_one_or_none()
    if not rep_db:
        raise HTTPException(status_code=404, detail="El repuesto no existe")

    # 3. Validar stock
    if rep_db.stock_actual < datos.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. En almacen tengo: {rep_db.stock_actual} y se solicitaron: {datos.cantidad}"
        )

    # Operacion transaccional
    rep_db.stock_actual -= datos.cantidad
    subtotal = rep_db.precio_venta * datos.cantidad
    orden_db.costo_reparacion += subtotal

    detalle = OrdenRepuestoModel(
        orden_id=orden_db.id,
        repuesto_id=rep_db.id,
        cantidad=datos.cantidad,
        precio_unitario_historico=rep_db.precio_venta
    )

    db.add(detalle)

    try:
        await db.commit()
        await db.refresh(detalle)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error aplicando la actualización parcial.")

    return detalle