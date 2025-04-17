# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({'message': 'Connected'}))

    async def receive(self, text_data):
        # Handle incoming messages if needed
        pass

    async def update_score(self, event):
        await self.send(text_data=json.dumps({'score': event['score']}))