"""Rutas HTTP, validación y exclusión de dos sesiones de mando."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
from aiohttp.test_utils import TestClient, TestServer
from aiohttp import WSServerHandshakeError, WSMsgType
import asyncio

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from servidor import crear_app


class Rutas(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import collections
        self.conductor=Mock()
        self.conductor.eventos=collections.deque()
        self.conductor.instantanea.return_value=dict(bateria=87,error=None)
        self.client=TestClient(TestServer(crear_app(self.conductor)))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()

    async def test_pagina_y_prueba_mando(self):
        for ruta in ['/', '/prueba_mando.html', '/clasico']:
            r=await self.client.get(ruta)
            self.assertEqual(r.status,200)
        r=await self.client.get('/audio/desconocido.ogg')
        self.assertEqual(r.status,404)

    async def test_cada_pagina_encuentra_sus_ficheros(self):
        # La interfaz nueva, la clásica y la librería 3D se sirven en local: sin internet en el laboratorio
        import re
        for ruta in ['/', '/clasico']:
            html=await (await self.client.get(ruta)).text()
            enlaces=re.findall(r'(?:src|href)="(/web/[^"]+)"',html)
            self.assertTrue(enlaces)
            self.assertNotIn('http://',html.replace('http://127.0.0.1',''))
            for enlace in enlaces:
                r=await self.client.get(enlace)
                self.assertEqual(r.status,200,enlace)
        escena=await (await self.client.get('/web/escena3d.js')).text()
        importado=re.search(r'from "(/web/vendor/[^"]+)"',escena).group(1)
        self.assertEqual((await self.client.get(importado)).status,200)

    async def test_sesion_unica_y_parada_al_cerrar(self):
        w=await self.client.ws_connect('/ws')
        self.assertEqual((await w.receive_json())['bateria'],87)
        await w.send_str('[]')
        error=await w.receive_json()
        while error['tipo']!='error':
            error=await w.receive_json()
        await w.close()
        self.conductor.parar.assert_called()

    async def test_la_pestana_nueva_toma_el_control(self):
        vieja=await self.client.ws_connect('/ws')
        await vieja.receive_json()
        nueva=await self.client.ws_connect('/ws')
        self.assertEqual((await nueva.receive_json())['bateria'],87)
        codigos=[]
        while True:                                   # la vieja recibe el cierre 4001
            m=await vieja.receive()
            if m.type==WSMsgType.CLOSE:
                codigos.append(m.data)
            if m.type in (WSMsgType.CLOSE,WSMsgType.CLOSED,WSMsgType.CLOSING,WSMsgType.ERROR):
                break
        self.assertEqual(codigos,[4001],m)
        llamadas=self.conductor.parar.call_count
        await asyncio.sleep(.1)                       # el cierre de la vieja no para a la nueva
        self.assertEqual(self.conductor.parar.call_count,llamadas)
        await nueva.send_str('[]')                    # la nueva sigue siendo la que manda
        m=await nueva.receive_json()
        while m['tipo']!='error':
            m=await nueva.receive_json()
        await nueva.close()

    async def test_rechaza_otro_origen(self):
        with self.assertRaises(WSServerHandshakeError):
            await self.client.ws_connect('/ws',headers={'Origin':'http://otro.invalid'})


if __name__=='__main__':
    unittest.main()
