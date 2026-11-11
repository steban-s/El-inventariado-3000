from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import obtener_bd
from models.mecanico import Mecanico
from schemas.schemas import MecanicoCreate, MecanicoResponse

router = APIRouter(prefix="/mecanicos", tags=["Mecánicos"])


@router.post("/", response_model=MecanicoResponse, status_code=status.HTTP_201_CREATED)
async def crear_mecanico(datos: MecanicoCreate, db: AsyncSession = Depends(obtener_bd)):
    nuevo = Mecanico(**datos.model_dump())
    db.add(nuevo)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un mecánico con ese documento")
    await db.refresh(nuevo)
    return nuevo


@router.get("/", response_model=List[MecanicoResponse])
async def listar_mecanicos(db: AsyncSession = Depends(obtener_bd)):
    resultado = await db.execute(select(Mecanico))
    return resultado.scalars().all()