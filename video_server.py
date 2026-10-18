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
