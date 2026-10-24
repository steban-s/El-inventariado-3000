from fastapi import FastAPI, HTTPException, Request
from comida import leer_base_datos, obtener_producto, guardar_base_datos, leer_taller, guardar_taller, db_lock
from api_post import ProductoCreate, OrdenCreate, OrdenUpdate

apiRest = FastAPI(
    title="API inventarios SENA",
    description="Mi primera API asíncrona",
    version="1.0.0"
)

@apiRest.get("/")
async def ruta_principal():
    return {"mensaje": "¡Bienvenido a mi primera API Rest!"}

@apiRest.get("/estado")
async def estado_servidor():
    return {"status": "En línea", "servicios": "Operativos sin ningun invonveniente"}

@apiRest.get("/productos")
async def listar_productos():
    datos = await leer_base_datos()
    return {"cantidad": len(datos), "productos": datos}

@apiRest.get("/productos/{codigo_producto}")
async def buscar_un_producto(codigo_producto: str):
    try:
        producto = await obtener_producto(codigo_producto)
        return producto
    except KeyError:
        raise HTTPException(status_code=404, detail="El producto soliciato no existe en la BD.")

@apiRest.post("/productos", status_code=201)
async def registrar_nuevo_producto(producto: ProductoCreate):
    datos = await leer_base_datos()

    for dato in datos:
        if dato["codigo"] == producto.codigo:
            raise HTTPException(status_code=400, detail="El código de producto ya existe.")

    nuevo_producto = producto.model_dump()

    datos.append(nuevo_producto)
    await guardar_base_datos(datos)

    return {"mensaje": "Producto registrado correctamente", "producto": nuevo_producto}

@apiRest.put("/productos/{codigo_producto}")
async def actulizar_producto(codigo_producto: str, producto_actualizado: ProductoCreate):
    datos = await leer_base_datos()
    for posicion, dato in enumerate(datos):
        if dato["codigo"] == codigo_producto:
            datos[posicion] = producto_actualizado.model_dump()
            datos[posicion]["codigo"] = codigo_producto

            await guardar_base_datos(datos)
            return {"mensaje": "Producto actualizado", "producto": datos[posicion]}
        
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@apiRest.post("/ordenes", status_code=201)
async def crear_orden(orden: OrdenCreate):
    async with db_lock:
        ordenes = await leer_taller()

        for o in ordenes:
            if o["placa"] == orden.placa and o["estado"] != "Entregada":
                raise HTTPException(status_code=400, detail="La moto ya se encuentra en el taller")

        nueva_orden = orden.model_dump()
        nueva_orden["estado"] = "En diagnóstico"
        nueva_orden["costo_reparacion"] = 0

        ordenes.append(nueva_orden)
        await guardar_taller(ordenes)
        return {"mensaje": "Orden creada correctamente", "orden": nueva_orden}

@apiRest.get("/ordenes")
async def listar_ordenes():
    ordenes = await leer_taller()
    return ordenes

@apiRest.put("/ordenes/{placa}")
async def actualizar_orden(placa: str, datos_nuevos: OrdenUpdate):
    async with db_lock:
        ordenes = await leer_taller()

        orden = None
        for o in reversed(ordenes):
            if o["placa"] == placa:
                orden = o
                break
        if orden is None:
            raise HTTPException(status_code=404, detail="Placa no encontrada")

        if datos_nuevos.nuevo_estado == "Reparada" and datos_nuevos.costo_reparacion <= 0:
            raise HTTPException(
                status_code=400,
                detail="No se puede marcar como reparada sin asignar un costo de reparación"
            )

        orden["estado"] = datos_nuevos.nuevo_estado
        orden["costo_reparacion"] = datos_nuevos.costo_reparacion

        await guardar_taller(ordenes)
        return {"mensaje": "Orden actualizada", "orden": orden}