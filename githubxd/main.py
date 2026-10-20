from fastapi import FastAPI, HTTPException
from comida import (leer_base_datos, obtener_categorias, buscar_por_nombre, obtener_stock_critico)


app = FastAPI(
    title="api inventarios Sena",
    description="mi primera chamba",
    version="1.0.0"
)

@app.get("/")
async def ruta_principal():
    return {"mensaje": "Bienvenido a mi primera chamba"}

@app.get("/estado")
async def estado_servidor():
    return {"status": "en linea", "servicios": "operativos"}

@app.get("/suma")
async def sumaxd():
    tres = 3
    dos = 2
    return {"resultado": tres + dos}

@app.get("/productos")
async def listar_productos():
    datos = await leer_base_datos()
    return datos 

@app.get("/producto/{codigo_producto}")
async def buscar_un_producto(codigo_producto: str):
    try:
        datos = await leer_base_datos()
        for dato in datos:
            if dato["codigo"] == codigo_producto:
                return dato
            raise KeyError("Producto no encontrado")
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Producto {codigo_producto} no encontrado")
      


@app.get("/categorias")
async def listar_categorias():
    return await obtener_categorias()


@app.get("/alertas/stock")
async def alertas_stock():
    return await obtener_stock_critico()


@app.get("/productos/buscar/{palabra_clave}")
async def buscar_productos(palabra_clave: str):
    return await buscar_por_nombre(palabra_clave)