from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json


class FlashairConsumer(WebsocketConsumer):

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'group1',
            self.channel_name
        )
        self.accept()
        # self.send(text_data=json.dumps({
        #     'message': 'Hi there',
        #     }))

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            'group1',
            self.channel_name
        )

    def receive(self):
        message = 'test message'
        self.send(text_data=json.dumps({
            'message': message,
            }))

    def group1_alarm(self, event):
        print('group1_alarm')
        self.send(json.dumps({
            'message': event['message']
            }))

