from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotifyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({'message': 'WebSocket connected!'}))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Echo back or handle custom logic
        await self.send(text_data=json.dumps({'message': data.get('message', '')}))

    # You can add group send methods for broadcast if needed