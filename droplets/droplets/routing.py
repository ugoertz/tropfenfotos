from channels.routing import ProtocolTypeRouter, URLRouter

import shoots.routing


application = ProtocolTypeRouter({
    'websocket': URLRouter(shoots.routing.websocket_urlpatterns),
})

