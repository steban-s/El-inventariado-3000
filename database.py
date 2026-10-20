import json
import aiofiles
import asyncio

ARCHIVO_BD = "pizzeria.json"
db_lock = asyncio.Lock()
alertas = []

async def leer_base_datos():
    try:
        async with aiofiles.open(ARCHIVO_BD, mode="r", encoding="utf-8") as f:
            contenido = await f.read()
            return json.loads(contenido)
    except FileNotFoundError:
        return []

async def guardar_base_datos(datos):
    async with aiofiles.open(ARCHIVO_BD, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(datos))

async def crear_producto(codigo, nombre, stock):
    async with db_lock:
        await asyncio.sleep(0.5)
        datos = await leer_base_datos()

        for dato in datos:
            if dato["codigo"] == codigo:
                raise ValueError(f"El producto con el código {codigo} ya existe.")

        nuevo_producto = {"codigo": codigo, "nombre": nombre, "stock": stock}
        datos.append(nuevo_producto)
        await guardar_base_datos(datos)
        return nuevo_producto

async def eliminar_producto(codigo):
    async with db_lock:
        await asyncio.sleep(0.5)
        datos = await leer_base_datos()

        nuevos_datos = [dato for dato in datos if dato["codigo"] != codigo]

        if len(datos) == len(nuevos_datos):
            raise KeyError(f"Producto {codigo} no ha sido encontrado.")

        await guardar_base_datos(nuevos_datos)
        return True

async def alerta_stock_bajo(codigo, nombre, stock_actual):
    await asyncio.sleep(2)
    print(f" El producto {nombre} ({codigo}) ha bajado a {stock_actual} unidades. Solicitar que se pongan a trabajar xd")

async def vender_producto(codigo, cantidad_vendida):
    async with db_lock:
        await asyncio.sleep(0.5)
        datos = await leer_base_datos()

        for dato in datos:
            if dato["codigo"] == codigo:
                if cantidad_vendida > dato["stock"]:
                    raise ValueError("Stock insuficiente")

                dato["stock"] -= cantidad_vendida
                await guardar_base_datos(datos)

                if dato["stock"] < 3:
                    tarea = asyncio.create_task(
                        alerta_stock_bajo(codigo, dato["nombre"], dato["stock"])
                    )
                    alertas.append(tarea)

                return {
                    "producto": dato["nombre"],
                    "cantidad_vendida": cantidad_vendida,
                    "stock_restante": dato["stock"]
                }

        raise KeyError("Producto no encontrado")