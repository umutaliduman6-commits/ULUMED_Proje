import asyncio
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from aiohttp import web, WSMsgType
import aiohttp_cors

UYGULAMA_DIZINI = Path(__file__).resolve().parent
VERITABANI_YOLU = Path(os.getenv('DATABASE_PATH', UYGULAMA_DIZINI / "ulumed_uyeler.db"))
PORT = int(os.getenv('PORT', 8080))


@web.middleware
async def onbellek_engelle(request, handler):
    # Arayüz güncellemelerinin tarayıcı/telefon önbelleğinde kalmaması için
    # HTML ve statik dosyalara "önbelleğe alma" başlığı ekliyoruz.
    response = await handler(request)
    if request.path == '/' or request.path.startswith('/static'):
        response.headers['Cache-Control'] = 'no-store, must-revalidate'
    return response


class VideoKonferansSunucusu:
    def __init__(self):
        self.app = web.Application(middlewares=[onbellek_engelle])
        self.oda_kullanicilari = {}
        self.setup_routes()
        self.setup_cors()
        self.veritabani_olustur()

    def veritabani_olustur(self):
        # Veritabanı dizinini oluştur
        VERITABANI_YOLU.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(VERITABANI_YOLU)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS odalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oda_adi TEXT NOT NULL,
                oda_kodu TEXT UNIQUE NOT NULL,
                olusturan TEXT,
                olusturma_zamani TEXT,
                durum TEXT DEFAULT 'Aktif'
            )
            """
        )
        conn.commit()
        conn.close()

    def setup_cors(self):
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        for route in list(self.app.router.routes()):
            cors.add(route)

    def setup_routes(self):
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/favicon.ico', self.favicon)
        self.app.router.add_get('/ws/{oda_kodu}', self.websocket_handler)
        self.app.router.add_post('/api/oda-olustur', self.oda_olustur)
        self.app.router.add_get('/api/oda/{oda_kodu}', self.oda_bilgisi)
        self.app.router.add_post('/api/uye-dogrula', self.uye_dogrula)
        self.app.router.add_static('/static', UYGULAMA_DIZINI / 'static')

    async def index(self, request):
        return web.FileResponse(UYGULAMA_DIZINI / 'static' / 'index.html')

    async def favicon(self, request):
        return web.Response(status=204)

    async def oda_olustur(self, request):
        try:
            data = await request.json()
            oda_adi = data.get('oda_adi', 'Görüşme Odası')
            olusturan = data.get('olusturan', 'Yönetici')

            oda_kodu = self.oda_kodu_uret()

            conn = sqlite3.connect(VERITABANI_YOLU)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO odalar (oda_adi, oda_kodu, olusturan, olusturma_zamani) VALUES (?, ?, ?, ?)",
                (oda_adi, oda_kodu, olusturan, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()

            # Request'ten host URL'ini al
            host = request.host
            scheme = request.scheme
            oda_linki = f'{scheme}://{host}?oda={oda_kodu}'

            return web.json_response({
                'success': True,
                'oda_kodu': oda_kodu,
                'oda_linki': oda_linki
            })
        except Exception as e:
            return web.json_response({'success': False, 'error': str(e)}, status=500)

    async def oda_bilgisi(self, request):
        oda_kodu = request.match_info.get('oda_kodu')
        conn = sqlite3.connect(VERITABANI_YOLU)
        cursor = conn.cursor()
        cursor.execute("SELECT oda_adi, olusturan, olusturma_zamani, durum FROM odalar WHERE oda_kodu = ?", (oda_kodu,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return web.json_response({
                'success': True,
                'oda_adi': result[0],
                'olusturan': result[1],
                'olusturma_zamani': result[2],
                'durum': result[3]
            })
        return web.json_response({'success': False, 'error': 'Oda bulunamadı'}, status=404)

    async def uye_dogrula(self, request):
        try:
            data = await request.json()
            telefon = data.get('telefon', '').strip()

            if not telefon:
                return web.json_response({'success': False, 'error': 'Telefon numarası gerekli'}, status=400)

            conn = sqlite3.connect(VERITABANI_YOLU)
            cursor = conn.cursor()

            # Telefon numarasını normalize et
            temiz_tel = ''.join(c for c in telefon if c.isdigit())
            if temiz_tel.startswith('90') and len(temiz_tel) == 12:
                temiz_tel = temiz_tel[2:]
            if temiz_tel.startswith('0') and len(temiz_tel) == 11:
                temiz_tel = temiz_tel[1:]

            # Veritabanında ara (telefon formatları)
            cursor.execute(
                "SELECT id, ad_soyad, telefon FROM uyeler WHERE telefon LIKE ? OR telefon LIKE ? OR telefon LIKE ?",
                (f'%{temiz_tel[-10:]}%', f'0{temiz_tel[-10:]}%', f'90{temiz_tel[-10:]}%')
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                return web.json_response({
                    'success': True,
                    'uye_id': result[0],
                    'ad_soyad': result[1],
                    'telefon': result[2]
                })
            else:
                return web.json_response({
                    'success': False,
                    'error': 'Bu telefon numarası kayıtlı üye değil'
                }, status=401)

        except Exception as e:
            return web.json_response({'success': False, 'error': str(e)}, status=500)

    def oda_kodu_uret(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

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

        # Yeni katılımcıyı odadaki diğer kullanıcılara bildir.
        # Bu mesajı alan istemciler yeni kullanıcıya WebRTC teklifi (offer) gönderir.
        for diger_ws in self.oda_kullanicilari[oda_kodu]:
            if diger_ws is not ws:
                await diger_ws.send_json({
                    'tip': 'user-joined',
                    'kullanici_id': uye_adi
                })

        await self.kullanici_listesi_gonder(oda_kodu)

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.mesaj_ilet(oda_kodu, ws, data)
                elif msg.type == WSMsgType.ERROR:
                    print(f'WebSocket error: {ws.exception()}')
        finally:
            kullanicilar = self.oda_kullanicilari.get(oda_kodu)
            if kullanicilar is not None:
                if ws in kullanicilar:
                    kullanicilar.remove(ws)
                
                # Ayrılan kullanıcıyı diğerlerine bildir
                for diger_ws in kullanicilar:
                    await diger_ws.send_json({
                        'tip': 'user-left',
                        'kullanici_id': uye_adi
                    })
                
                await self.kullanici_listesi_gonder(oda_kodu)

                if not self.oda_kullanicilari.get(oda_kodu):
                    self.oda_kullanicilari.pop(oda_kodu, None)

        return ws

    async def mesaj_ilet(self, oda_kodu, gonderen_ws, data):
        # Gönderenin adını mesaja ekle; karşı taraf yanıtı kime göndereceğini bilsin
        gonderen_id = getattr(gonderen_ws, 'kullanici_id', None)
        data['gonderen'] = gonderen_id
        
        tip = data.get('tip')
        hedef = data.get('hedef')
        
        print(f"Mesaj iletiliyor: Tip={tip}, Gönderen={gonderen_id}, Hedef={hedef}")

        hedef_ws = None
        if hedef:
            for ws in self.oda_kullanicilari[oda_kodu]:
                if getattr(ws, 'kullanici_id', None) == hedef:
                    hedef_ws = ws
                    break

        if hedef_ws:
            await hedef_ws.send_json(data)
        elif hedef:
            print(f"Hedef bulunamadı: {hedef}")
            return
        else:
            # Broadcast (hedef belirtilmemişse)
            for ws in self.oda_kullanicilari[oda_kodu]:
                if ws != gonderen_ws:
                    await ws.send_json(data)

    async def kullanici_listesi_gonder(self, oda_kodu):
        baglantilar = self.oda_kullanicilari.get(oda_kodu, [])
        kullanicilar = [getattr(ws, 'kullanici_id', 'Anonim') for ws in baglantilar]

        mesaj = {'tip': 'kullanici_listesi', 'kullanicilar': kullanicilar}
        for ws in baglantilar:
            await ws.send_json(mesaj)

    def run(self, host='0.0.0.0', port=8080):
        web.run_app(self.app, host=host, port=port)


if __name__ == '__main__':
    sunucu = VideoKonferansSunucusu()
    sunucu.run()
