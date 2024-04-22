import asyncio
import websockets
import json
import random

server_ip = '0.0.0.0'
server_port = 9009
pelotas = []
estado_global = {}
clientes = set()
contador_jugadores = 0
jugadores_listos = 0
puntos_jugador_izquierdo = 0
puntos_jugador_derecho = 0
jugadores_izquierda = 0
jugadores_derecha = 0
juego_terminado = False

def verificar_todos_listos():
    global todos_listos
    todos_listos = all(jugador['ready'] for jugador in estado_global.values())

async def generar_pelotas():
    intervalo = 1

    while True:
        if clientes and todos_listos:
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
    global contador_jugadores, jugadores_izquierda, jugadores_derecha, juego_terminado
    id_jugador = contador_jugadores
    contador_jugadores += 1
    
    if jugadores_izquierda <= jugadores_derecha:
        estado_global[id_jugador] = {'x': 100, 'y': 300, 'ready': False}
        jugadores_izquierda += 1
    else:
        estado_global[id_jugador] = {'x': 700, 'y': 300, 'ready': False}
        jugadores_derecha += 1
        
    await websocket.send(str(id_jugador))
    
    clientes.add(websocket)
    print(f"Player {id_jugador} se ha unido al servidor.")
    
    try:
        while True:
            datos = await websocket.recv()
            movimiento = json.loads(datos)
            estado_global[id_jugador] = movimiento
            
            if not movimiento['ready']:
                pelotas.clear()

    except websockets.ConnectionClosed:
        print(f"La conexión con el cliente {id_jugador} ha sido cerrada inesperadamente.")
    finally:
        clientes.remove(websocket)
        if id_jugador in estado_global:
            del estado_global[id_jugador]
            print(f"Player {id_jugador} ha sido eliminado")
            if id_jugador in estado_global:
                if estado_global[id_jugador]['x'] == 100:
                    jugadores_izquierda -= 1
                else:
                    jugadores_derecha -= 1
        juego_terminado = False

def verificar_colisiones():
    global puntos_jugador_izquierdo, puntos_jugador_derecho, juego_terminado
    for id_jugador, jugador in list(estado_global.items()):
        if 'x' in jugador and 'y' in jugador:
            x_jugador = jugador['x']
            y_jugador = jugador['y']
        
            for pelota in pelotas:
                x_pelota = pelota['x']
                y_pelota = pelota['y']
            
                if (x_jugador < x_pelota + 20 and x_jugador + 87 > x_pelota and
                    y_jugador < y_pelota + 20 and y_jugador + 120 > y_pelota):
                    pelota['velocidad_x'] *= -1  
                    pelota['velocidad_y'] *= random.choice([-1, 1]) 
                
                if x_pelota < 0 or x_pelota > 850:
                    juego_terminado = True 

                if y_pelota < 10 or y_pelota > 520:
                    pelota['velocidad_y'] *= -1

async def actualizar_estado():
    while True:
        verificar_todos_listos()

        if todos_listos:
            asyncio.create_task(generar_pelotas())
        
        if todos_listos:
            verificar_colisiones()
        
        for pelota in pelotas:
            pelota['x'] += pelota['velocidad_x']
            pelota['y'] += pelota['velocidad_y']

        estado = {
            'estado_global': estado_global,
            'pelotas': pelotas,
            'puntos_jugador_izquierdo': puntos_jugador_izquierdo,
            'puntos_jugador_derecho': puntos_jugador_derecho,
            'juego_terminado': juego_terminado
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