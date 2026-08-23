# Liman Gayrimenkul

Türkiye & KKTC emlak danışmanlığı sitesi — gerçek Flask backend'i, SQLite veritabanı,
admin paneli ve favoriler sistemiyle tam çalışan bir proje.

## Özellikler

- **Gerçek ilan verisi** — SQLite veritabanından geliyor, sayfa yüklenince `/api/listings`'den çekiliyor
- **İnteraktif Türkiye + KKTC haritası** — gerçek il sınırları, bölgeye tıkla → yakınlaş → şehir seç → ilanlar filtrelensin
- **Filtreleme** — bölge, emlak tipi, segment, şehir (hepsi backend verisine göre çalışıyor)
- **Admin paneli** (`/admin`) — ilan ekle / düzenle / sil, gelen mesajları gör ve okundu işaretle
- **Gerçek iletişim formu** — mesajlar veritabanına kaydediliyor, admin panelinden görülüyor
- **Favoriler** — kalp ikonuyla işaretle, tarayıcıda kalıcı (localStorage), "Favorilerim" filtresiyle sadece onları göster
- Bölge chip'lerindeki ve hero'daki "Aktif İlan" sayısı gerçek veriden hesaplanıyor

## Kurulum

```bash
# 1) Sanal ortam oluştur (opsiyonel ama önerilir)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2) Bağımlılıkları kur
pip install -r requirements.txt

# 3) Çalıştır
python app.py
```

Site `http://127.0.0.1:5000` adresinde açılır. İlk çalıştırmada `liman.db` dosyası
otomatik oluşur ve 8 örnek ilanla doldurulur (`seed_if_empty()` fonksiyonu).


Aynı şekilde `SECRET_KEY` ortam değişkenini de gerçek bir projede mutlaka değiştir
(session imzalama anahtarı — `app.py` içindeki `dev-secret-degistir-bunu` sadece
geliştirme içindir).

## Proje Yapısı

```
liman-app/
├── app.py                        # Flask backend: modeller, API, admin CRUD
├── requirements.txt
├── liman.db                      # SQLite veritabanı (ilk çalıştırmada oluşur)
├── templates/
│   ├── index.html                # Ana site (veriyi fetch ile /api/listings'den çeker)
│   ├── admin_login.html
│   └── admin_dashboard.html
└── README.md
```

## API Uçları

| Yöntem | Yol                              | Açıklama                                   |
|--------|-----------------------------------|---------------------------------------------|
| GET    | `/api/listings`                   | Tüm ilanlar (query: `region`, `city`, `type`, `tier`) |
| POST   | `/api/contact`                    | İletişim formu mesajı kaydeder             |
| GET    | `/admin`                          | Dashboard (giriş gerektirir)                |
| POST   | `/admin/listings/new`             | Yeni ilan ekler                             |
| POST   | `/admin/listings/<id>/edit`       | İlanı günceller                             |
| POST   | `/admin/listings/<id>/delete`     | İlanı siler                                 |
| POST   | `/admin/messages/<id>/read`       | Mesajı okundu işaretler                     |
| POST   | `/admin/messages/<id>/delete`     | Mesajı siler                                |

## Sonraki adımlar (istersen)

- **Deploy:** Render, Railway veya bir VPS'e taşımak için `gunicorn` ekleyip
  `Procfile` yazman yeterli — ortam değişkenlerini (`SECRET_KEY`, `ADMIN_PASSWORD`)
  orada da ayarlamayı unutma.
- **E-posta bildirimi:** `/api/contact` içine bir SMTP entegrasyonu eklenip yeni
  mesaj geldiğinde sana mail atılabilir.
- **Görsel yükleme:** İlanlara gerçek fotoğraf eklemek istersen `Listing` modeline
  bir `image_url` alanı eklenip admin formuna dosya yükleme eklenebilir.
