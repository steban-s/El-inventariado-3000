import asyncio
from database import crear_producto, eliminar_producto, vender_producto, alertas

async def venta(codigo, cantidad):
    try:
        resultado = await vender_producto(codigo, cantidad)
        print(f"Venta exitosa: {resultado}")
    except KeyError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")

async def prueba_de_estres():
    print("--- Iniciando prueba ---")

    for codigo in ("P001", "P002", "P003"):
        try:
            await eliminar_producto(codigo)
        except KeyError:
            pass

    try:
        await asyncio.gather(
            crear_producto("P001", "Pizza Hawaiana", 10),
            crear_producto("P002", "Pizza Pepperoni", 5),
            crear_producto("P003", "Pizza Margarita", 4),
        )
        print("Productos creados exitosamente")
    except Exception as e:
        print(f"Error de creación: {e}")

    print("\nProcesando 4 ventas simultáneas...")
    await asyncio.gather(
        venta("P001", 2),
        venta("P002", 3),
        venta("P003", 10),
        venta("P999", 1),
    )

    if alertas:
        await asyncio.gather(*alertas)

asyncio.run(prueba_de_estres())