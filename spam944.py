import asyncio
import random
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError
from telethon import events
import os
import requests
from datetime import datetime, timedelta

# Configuración del cliente
API_ID = 24994755
API_HASH = "83c4d6c5ab28171766cb4b67f900d185"
PHONE_NUMBER = "+51944865840"
SESSION_NAME = "bot_session"

# Intervalo entre envíos (en segundos)
MIN_INTERVAL = 10  # Mínimo tiempo de espera
MAX_INTERVAL = 350  # Máximo tiempo de espera
SPAM_GROUP_NAME = "spam bot"
CONTROL_GROUP_NAME = "spam bot control"

# Lista de grupos a excluir
EXCLUDED_GROUPS = [
    "TRABAJOS LABS 🧑‍💻",
    "👨🏻‍💻GRUPO GENERAL👨🏻‍💻",
    "Admins >🎖 【𝙻𝙻™】 🎖",
    "Usuarios Valiosos [LINK] 02",
    "�𝙏𝘼𝙁𝙁 𝘿𝙀 𝙇𝙊𝙎 𝙂𝙍𝙐𝙋𝙊𝙎"
]

# Memoria de mensajes enviados para controlar el límite
message_memory = {}
MESSAGE_LIMIT = 4  # Máximo de mensajes automáticos por usuario
MESSAGE_TIMEOUT = timedelta(hours=24)  # Tiempo para reiniciar el contador

async def reconnect(client):
    """Intentar reconectar automáticamente si la conexión se pierde."""
    while not client.is_connected():
        try:
            await client.connect()
            print("Reconexión exitosa.")
        except Exception as e:
            print(f"Reconexión fallida: {e}. Reintentando en 5 segundos...")
            await asyncio.sleep(5)

@events.register(events.NewMessage(incoming=True))
async def handle_new_private_message(event):
    """Responde automáticamente a nuevos mensajes privados."""
    if event.is_private:
        user_id = event.sender_id
        now = datetime.now()

        # Revisar si el usuario está en la memoria
        if user_id in message_memory:
            last_sent, message_count = message_memory[user_id]

            # Verificar si ha pasado el tiempo límite
            if now - last_sent > MESSAGE_TIMEOUT:
                message_memory[user_id] = (now, 1)  # Reiniciar contador
            elif message_count >= MESSAGE_LIMIT:
                print(f"Límite de mensajes alcanzado para {user_id}")
                return
            else:
                message_memory[user_id] = (now, message_count + 1)
        else:
            message_memory[user_id] = (now, 1)  # Agregar nuevo usuario

        try:
            await event.reply(
                "**Hola!** 😊 **Clickeame y escríbeme a mi perfil principal para atenderte de inmediato!**\n\n"
                "[👉 **Haz clic aquí abajo** 👇](https://t.me/Asteriscom)",
                link_preview=True
            )
            print(f"Mensaje automático enviado a {user_id}")
        except Exception as e:
            print(f"Error al enviar mensaje automático a {user_id}: {e}")

async def send_messages_to_groups(client):
    """Reenvía mensajes desde el grupo 'spam bot' a otros grupos."""
    group_ids = []
    control_group_id = None

    # Obtiene los IDs de los grupos de destino y el grupo de control
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            if dialog.name == CONTROL_GROUP_NAME:
                control_group_id = dialog.id
            elif dialog.name != SPAM_GROUP_NAME and dialog.name not in EXCLUDED_GROUPS:
                group_ids.append(dialog.id)

    if control_group_id is None:
        print("No se encontró el grupo de control.")
        return

    # Itera sobre los mensajes en el grupo 'spam bot'
    while True:
        await reconnect(client)  # Asegurarse de estar conectado
        async for dialog in client.iter_dialogs():
            if dialog.is_group and dialog.name == SPAM_GROUP_NAME:
                async for message in client.iter_messages(dialog, limit=10):
                    for group_id in group_ids:
                        try:
                            await client.forward_messages(group_id, [message])
                            group_name = (await client.get_entity(group_id)).title
                            print(f"\033[92mMensaje reenviado al grupo {group_name}\033[0m")
                            await client.send_message(control_group_id, f"Mensaje reenviado a: {group_name}")
                        except FloodWaitError as e:
                            print(f"\033[91mDemasiados mensajes enviados. Esperando {e.seconds} segundos...\033[0m")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            print(f"\033[91mError al reenviar mensaje al grupo {group_id}: {e}\033[0m")
                            await client.send_message(control_group_id, f"Error al reenviar mensaje al grupo {group_id}.")
                        # Pausa entre reenvíos de mensajes
                        interval = random.randint(MIN_INTERVAL, MAX_INTERVAL)
                        await asyncio.sleep(interval)
        # Pausa antes de verificar nuevos mensajes
        await asyncio.sleep(10)

async def main():
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await reconnect(client)
        if not await client.is_user_authorized():
            await client.send_code_request(PHONE_NUMBER)
            await client.sign_in(PHONE_NUMBER, input("Ingresa el código enviado a tu teléfono: "))

        print("Bot conectado exitosamente.")
        client.add_event_handler(handle_new_private_message)
        await send_messages_to_groups(client)

if __name__ == "__main__":
    asyncio.run(main())
