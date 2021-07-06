from aiohttp import web, streamer
import aiohttp
import socketserver
import socket
import asyncio
import websockets
import threading
import logging

from .keys import Keys

_LOGGER = logging.getLogger(__name__)


class WebServer():
    def __init__(self, panel):
        self._panel = panel
        self._msg_queue = asyncio.Queue()

    def _run_thread(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            pass

    def start(self, port):
        self._loop = asyncio.get_event_loop()

        # Set up the HTTP server
        app = web.Application()
        
        app.router.add_get('/', self._root_handler)
        app.router.add_get('/ws', self._websocket_handler)

        runner = web.AppRunner(app)
        self._loop.run_until_complete(runner.setup())

        site = web.TCPSite(runner, '0.0.0.0', port)
        self._loop.run_until_complete(site.start())

        _LOGGER.info('listening on port %d', port)

        t = threading.Thread(target=self._run_thread)
        t.start();

    def text_updated(self, text):
        self._loop.call_soon_threadsafe(self._msg_queue.put_nowait, text)

    async def _root_handler(self, request):
        s = open('aqualogic/web.html', 'r')
        return web.Response(text=s.read(), content_type='text/html')

    async def _websocket_handler(self, request):
        # Websocket handler for providing the live data
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)
        _LOGGER.info('Websocket connection ready')

        consumer_task = asyncio.ensure_future(self._consumer_handler(ws))
        producer_task = asyncio.ensure_future(self._producer_handler(ws))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

        _LOGGER.info('Websocket connection closed')
        return ws

    async def _consumer_handler(self, ws):
        async for msg in ws:
            try:
                key = Keys[msg.data]
                self._panel.send_key(key)
            except KeyError:
                _LOGGER.info('Invalid key name {}'.format(msg.data))

    async def _producer_handler(self, ws):
        while not ws.closed:
            text = await self._msg_queue.get()
            await ws.send_str(text)
            self._msg_queue.task_done()
