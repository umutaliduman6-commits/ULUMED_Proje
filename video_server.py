async def uye_dogrula(self, request):
    # Üye doğrulama geçici olarak devre dışı
    return web.json_response({
        'success': True,
        'uye_id': 'guest',
        'ad_soyad': 'Guest User',
        'telefon': '0000000000'
    })
