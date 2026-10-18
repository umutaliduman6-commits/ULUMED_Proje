async def websocket_handler(self, request):
    oda_kodu = request.match_info.get('oda_kodu')
    uye_adi = request.query.get('uye_adi')

    if not uye_adi:
        return web.Response(status=400, text="Ad gerekli")

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    if oda_kodu not in self.oda_kullanicilari:
        self.oda_kullanicilari[oda_kodu] = []

    ws.kullanici_id = uye_adi
    self.oda_kullanicilari[oda_kodu].append(ws)
    await self.kullanici_listesi_gonder(oda_kodu)

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self.mesaj_ilet(oda_kodu, ws, data)
            elif msg.type == WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    finally:
        if ws in self.oda_kullanicilari[oda_kodu]:
            self.oda_kullanicilari[oda_kodu].remove(ws)
        await self.kullanici_listesi_gonder(oda_kodu)

        if not self.oda_kullanicilari[oda_kodu]:
            del self.oda_kullanicilari[oda_kodu]

    return ws
