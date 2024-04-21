import asyncio
import websockets
import pygame
from pygame.locals import *
import json

server_ip = '44.196.162.180'
server_port = 9009

pygame.init()
screen = pygame.display.set_mode((850, 530))
clock = pygame.time.Clock()

font = pygame.font.Font(None, 20)

estado_jugador = {'x': 50, 'y': 300, 'ready': False}  

estado_global = {}
pelotas = []

async def actualizar_estado(websocket):
    global estado_global, pelotas

    data = await websocket.recv()
    if data:
        estado = json.loads(data)
        estado_global = estado['estado_global']
        pelotas = estado.get('pelotas', [])

async def enviar_movimiento(websocket):
    await websocket.send(json.dumps(estado_jugador))
    await actualizar_estado(websocket)

async def main():
    async with websockets.connect(f"ws://{server_ip}:{server_port}") as websocket:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN and event.key == K_c:  
                    estado_jugador['ready'] = not estado_jugador['ready']
                    await enviar_movimiento(websocket)
            
            keys = pygame.key.get_pressed()
            
            if keys[K_UP] and estado_jugador['y'] > 0:
                estado_jugador['y'] -= 20
            if keys[K_DOWN] and estado_jugador['y'] < 510:
                estado_jugador['y'] += 20

            await enviar_movimiento(websocket)

            screen.fill((0, 128, 0))  

            for id_jugador, pos in estado_global.items():
                pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(pos['x'], pos['y'], 20, 120)) 
                
            for pelota_info in pelotas:
                pelota_info['x'] -= 50
                pygame.draw.circle(screen, (255, 0, 0), (int(pelota_info['x']), int(pelota_info['y'])), 10) 

            mensaje_texto = font.render("Todos los jugadores opriman c para comenzar", True, (255, 255, 255))
            screen.blit(mensaje_texto, ((screen.get_width() - mensaje_texto.get_width()) // 2, 10))

            pygame.display.update()

            clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
