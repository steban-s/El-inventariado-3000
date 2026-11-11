from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import obtener_bd
from models.repuesto import Repuesto
from schemas.schemas import RepuestoCreate, RepuestoResponse

router = APIRouter(prefix="/repuestos", tags=["Repuestos"])


@router.post("/", response_model=RepuestoResponse, status_code=status.HTTP_201_CREATED)
async def crear_repuesto(datos: RepuestoCreate, db: AsyncSession = Depends(obtener_bd)):
    nuevo = Repuesto(**datos.model_dump())
    db.add(nuevo)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un repuesto con ese código SKU")
    await db.refresh(nuevo)
    return nuevo


@router.get("/", response_model=List[RepuestoResponse])
async def listar_repuestos(db: AsyncSession = Depends(obtener_bd)):
    resultado = await db.execute(select(Repuesto))
    return resultado.scalars().all()