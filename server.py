import asyncio
import websockets
import json
import random

server_ip = '0.0.0.0'
server_port = 9009
clientes = set()
estado_global = {}
contador_jugadores = 0
pelotas = []
tiempo_restante = 0
puntos_jugador_izquierdo = 0
puntos_jugador_derecho = 0

def verificar_todos_listos():
    global todos_listos
    todos_listos = all(jugador['ready'] for jugador in estado_global.values())

async def generar_pelotas():
    intervalo = 1

    while True:
        if clientes and todos_listos and tiempo_restante > 0:
            if not pelotas:
                pelota = {
                    'x': 425,
                    'y': 265,
                    'velocidad_x': random.uniform(-6, -15),
                    'velocidad_y': random.choice([-1, 1])  
                }
                pelotas.append(pelota)
        
        await asyncio.sleep(intervalo)

async def manejar_cliente(websocket, path):
    global contador_jugadores, tiempo_restante
    id_jugador = contador_jugadores
    contador_jugadores += 1
    
    if len(estado_global) == 0:
        estado_global[id_jugador] = {'x': 50, 'y': 300, 'ready': False}
    else:
        estado_global[id_jugador] = {'x': 800, 'y': 300, 'ready': False}
        
    await websocket.send(json.dumps(estado_global[id_jugador]))
    
    clientes.add(websocket)
    print(f"Player {id_jugador} ha sido conectado")

    try:
        while True:
            datos = await websocket.recv()
            movimiento = json.loads(datos)
            estado_global[id_jugador] = movimiento
            
            if not movimiento['ready'] and tiempo_restante > 0:
                tiempo_restante = 0
                pelotas.clear()

    except websockets.ConnectionClosed:
        print(f"La conexión con el cliente {id_jugador} ha sido cerrada inesperadamente.")
    finally:
        clientes.remove(websocket)
        if id_jugador in estado_global:
            del estado_global[id_jugador]
            print(f"Player {id_jugador} ha sido eliminado")

def verificar_colisiones():
    global tiempo_restante, puntos_jugador_izquierdo, puntos_jugador_derecho
    for id_jugador, jugador in estado_global.items():
        x_jugador = jugador['x']
        y_jugador = jugador['y']
        
        for pelota in pelotas:
            x_pelota = pelota['x']
            y_pelota = pelota['y']
            
            if (x_jugador < x_pelota + 20 and x_jugador + 87 > x_pelota and
                y_jugador < y_pelota + 20 and y_jugador + 120 > y_pelota):
                pelota['velocidad_x'] *= -1  
                pelota['velocidad_y'] *= random.choice([-1, 1])  

            if x_pelota < 0:
                puntos_jugador_derecho += 1
                pelota['x'] = 425
                pelota['y'] = 265
                pelota['velocidad_x'] *= -1
            elif x_pelota > 900:
                puntos_jugador_izquierdo += 1
                pelota['x'] = 425
                pelota['y'] = 265
                pelota['velocidad_x'] *= -1

            if y_pelota < 0 or y_pelota > 530:
                pelota['velocidad_y'] *= -1

async def actualizar_estado():
    global tiempo_restante

    while True:
        verificar_todos_listos()

        if todos_listos and tiempo_restante == 0:
            tiempo_restante = 120
            asyncio.create_task(generar_pelotas())
        
        if todos_listos and tiempo_restante > 0:
            tiempo_restante -= 0.1
            verificar_colisiones()

            if tiempo_restante <= 0:
                tiempo_restante = 0
                pelotas.clear()
        
        for pelota in pelotas:
            pelota['x'] += pelota['velocidad_x']
            pelota['y'] += pelota['velocidad_y']

        pelotas[:] = [pelota for pelota in pelotas if pelota['x'] > 0]

        estado = {
            'estado_global': estado_global,
            'pelotas': pelotas,
            'tiempo_restante': tiempo_restante,
            'puntos_jugador_izquierdo': puntos_jugador_izquierdo,
            'puntos_jugador_derecho': puntos_jugador_derecho
        }

        estado_json = json.dumps(estado)
        
        if clientes:
            tareas = [asyncio.create_task(cliente.send(estado_json)) for cliente in clientes if cliente.open]
            if tareas:
                await asyncio.wait(tareas)

        await asyncio.sleep(0.1)

start_server = websockets.serve(manejar_cliente, server_ip, server_port)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.create_task(actualizar_estado())
loop.run_forever()
