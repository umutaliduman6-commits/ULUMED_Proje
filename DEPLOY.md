# ULUMED Video Konferans - Render.com Deploy Talimatları

## Ön Hazırlık

### 1. GitHub Repository Oluşturun

```bash
# Git başlat
git init

# .gitignore eklendi - veritabanı hariç her şeyi yükle
git add .
git commit -m "Initial commit: Video konferans sistemi"

# GitHub'da yeni repository oluşturun
# Ardından:
git remote add origin https://github.com/KULLANICI_ADINIZ/ulumed-video.git
git branch -M main
git push -u origin main
```

### 2. Render.com Hesabı Oluşturun

1. [render.com](https://render.com) adresine gidin
2. "Sign Up" ile kayıt olun (GitHub ile bağlayın)
3. Email doğrulaması yapın

---

## Render.com Deploy

### Adım 1: Yeni Web Service Oluşturun

1. Render dashboard'da "New +" → "Web Service" tıklayın
2. GitHub repository'nizi seçin
3. "Connect" butonuna tıklayın

### Adım 2: Yapılandırma

Aşağıdaki ayarları yapın:

**Name:** `ulumed-video-server`

**Environment:** `Python`

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
python video_server.py
```

**Plan:** `Free`

**Instance Type:** `Free`

### Adım 3: Environment Variables

Aşağıdaki environment variable'ları ekleyin:

| Key | Value |
|-----|-------|
| PORT | 8080 |

### Adım 4: Deploy

"Create Web Service" butonuna tıklayın.

Deploy süresi: ~2-5 dakika

---

## Deploy Sonrası

### 1. URL Alın

Deploy tamamlandığında Render size bir URL verecek:
```
https://ulumed-video-server.onrender.com
```

### 2. ULUMED Uygulamasını Güncelleyin

`ulumed_yonetim.py` dosyasında URL'yi güncelleyin:

**Yöntem 1: Hardcoded URL (Basit)**

```python
# video_konferans_baslat fonksiyonunda bulun
# Eski (lokal)
url = 'http://localhost:8080/api/oda-olustur'

# Yeni (Render)
VIDEO_SERVER_URL = 'https://ulumed-video-server.onrender.com'
url = f'{VIDEO_SERVER_URL}/api/oda-olustur'
```

**Yöntem 2: Environment Variable (Önerilen)**

`.env` dosyası oluşturun:
```
VIDEO_SERVER_URL=https://ulumed-video-server.onrender.com
```

`ulumed_yonetim.py`'ye ekleyin:
```python
import os
from dotenv import load_dotenv

load_dotenv()
VIDEO_SERVER_URL = os.getenv('VIDEO_SERVER_URL', 'http://localhost:8080')
```

Kullanım:
```python
url = f'{VIDEO_SERVER_URL}/api/oda-olustur'
```

### 3. Test Edin

```bash
# Browser'da açın
https://ulumed-video-server.onrender.com
```

---

## Veritabanı Yönetimi

⚠️ **Önemli:** Render free tier disk saklamaz. Her deploy'da veritabanı sıfırlanır.

### Çözüm 1: PostgreSQL (Önerilen)

Render'da ücretsiz PostgreSQL oluşturun:

1. Dashboard → "New +" → "PostgreSQL"
2. Name: `ulumed-db`
3. Plan: Free
4. Create

Database URL'i alın ve environment variable olarak ekleyin:
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

`video_server.py`'yi PostgreSQL kullanacak şekilde güncelleyin.

### Çözüm 2: Lokal Veritabanı

Lokal ULUMED uygulaması ile veritabanı paylaşın:
- ULUMED uygulamasını çalıştıran bilgisayarda
- video_server.py aynı veritabanını kullansın

---

## TURN Server (Opsiyonel)

Farklı ağlardaki kullanıcılar için TURN server önerilir.

### Ücretsiz TURN Server

1. [coturn](https://github.com/coturn/coturn) kurun
2. Render'a deploy edin veya başka bir VPS'te çalıştırın
3. `static/index.html`'de ICE servers'ı güncelleyin:

```javascript
const config = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
        {
            urls: 'turn:your-turn-server.com:3478',
            username: 'your-username',
            credential: 'your-credential'
        }
    ]
};
```

---

## Güvenlik Kontrol Listesi

- [x] HTTPS aktif (Render otomatik sağlar)
- [x] CORS ayarları yapıldı
- [x] Üye doğrulama aktif
- [ ] TURN server eklendi (opsiyonel)
- [ ] Rate limiting eklendi (opsiyonel)
- [ ] Log monitoring aktif (Render dashboard)

---

## Sorun Giderme

### Deploy Başarısız

**Sorun:** Build failed

**Çözüm:**
1. Render logs'ı kontrol edin
2. `requirements.txt` doğru olduğundan emin olun
3. Python versiyonu kontrol edin (3.11+)

### Veritabanı Hatası

**Sorun:** Database connection failed

**Çözüm:**
1. PostgreSQL kullanın (çözüm 1)
2. Veya lokal veritabanı paylaşın (çözüm 2)

### WebRTC Bağlantı Sorunu

**Sorun:** Video bağlantısı kurulamıyor

**Çözüm:**
1. HTTPS olduğundan emin olun
2. TURN server ekleyin
3. Browser console'da hataları kontrol edin

---

## Maliyet

**Render Free Tier:**
- ✅ Web Service: Bedava
- ✅ PostgreSQL: Bedava (90 gün, sonra $7/ay)
- ✅ SSL: Bedava
- ✅ Bandwidth: 100GB/ay

**Toplam:** Ücretsiz (küçük kullanım için)

---

## Sonraki Adımlar

1. ✅ Deploy tamamlandı
2. ✅ Test edildi
3. 📝 Kullanıcı geri bildirimleri al
4. 🔄 Gerekirse TURN server ekle
5. 📊 Monitoring ve logging ayarla
6. 🔒 Güvenlik testleri yap

---

## Destek

Sorun yaşarsanız:
- Render docs: https://render.com/docs
- WebRTC docs: https://webrtc.org
- GitHub Issues: Repository'nizde issue açın
