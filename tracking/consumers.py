import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.tracking_token = self.scope['url_route']['kwargs']['tracking_token']
        self.group_name = f"order_tracking_{self.order_id}_{self.tracking_token}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"[Connected] Group: {self.group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"[Disconnected] Group: {self.group_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        # ✅ Rider sends their current location
        print(f"[Received] Lat: {latitude}, Lng: {longitude} for {self.group_name}")

        # ✅ Broadcast to all in the group (only the related customer sees this)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_location",
                "latitude": latitude,
                "longitude": longitude
            }
        )

    async def send_location(self, event):
        await self.send(text_data=json.dumps({
            "latitude": event["latitude"],
            "longitude": event["longitude"]
        }))
