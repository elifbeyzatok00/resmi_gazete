# Resmi Gazete MCP Server

Bu proje, Resmi Gazete verilerini otomatik olarak çeken ve işleyen bir **MCP (Model Context Protocol)** sunucusudur. LLM'lerin (Büyük Dil Modelleri) Resmi Gazete içeriklerine erişmesini sağlayan bir araç (tool) olarak çalışır.

## 📋 İçindekiler

- [Genel Bakış](#genel-bakış)
- [LLM ve MCP Hakkında](#llm-ve-mcp-hakkında)
- [Nasıl Çalışır](#nasıl-çalışır)
- [Kullanılan Teknolojiler](#kullanılan-teknolojiler)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Özellikler](#özellikler)
- [Mimari](#mimari)

## 🎯 Genel Bakış

Bu sistem, belirli bir tarih aralığındaki Resmi Gazete yayınlarını otomatik olarak toplar, işler ve yapılandırılmış bir formatta sunar. Hem HTML hem de PDF formatındaki içerikleri destekler ve taranmış PDF'ler için OCR (Optik Karakter Tanıma) özelliği içerir.

## 🤖 LLM ve MCP Hakkında

### LLM Bu Sistemde Var mı?

**HAYIR** - Bu sistem kendi içinde bir LLM içermez. Bu bir **MCP Tool Server**'dır, yani:

- **LLM'ler bu sistemi kullanır** (Claude, GPT vb.)
- Sistem, LLM'lere Resmi Gazete verilerine erişim yetkisi veren bir **araç/tool** sağlar
- LLM'ler bu tool'u çağırarak güncel Resmi Gazete içeriklerini alabilir

### MCP (Model Context Protocol) Nedir?

MCP, LLM'lerin dış kaynaklara ve araçlara standart bir şekilde erişmesini sağlayan bir protokoldür. Bu sistem, MCP standardına uygun bir tool sunarak LLM'lerin:

- Resmi Gazete verilerini sorgulamasını
- Tarih aralıklarını belirlemesini
- HTML ve PDF içeriklerini almasını

mümkün kılar.

## ⚙️ Nasıl Çalışır

### Çalışma Akışı

1. **Tarih Aralığı Belirleme**
   - Kullanıcı (veya LLM) başlangıç ve bitiş tarihi belirtir
   - Sistem bu aralıktaki her gün için URL'ler oluşturur

2. **HTML İçerik Çekme**
   - Tavily API kullanılarak her günün HTML sayfası çekilir
   - HTML içerik parse edilir ve raw content elde edilir

3. **PDF İşleme**
   - Her gün için PDF URL'i oluşturulur
   - PDF dosyası indirilir
   - PyPDF2 ile metin çıkarılır
   - Eğer PDF taranmış/görsel ise OCR devreye girer

4. **OCR Desteği**
   - Taranmış PDF'ler tespit edilir (garbled text kontrolü)
   - pdf2image ile PDF sayfalar görsel'e dönüştürülür
   - pytesseract ile Türkçe ve İngilizce OCR yapılır
   - Her sayfa için metin çıkarılır

5. **Sonuç Döndürme**
   - Tüm veriler JSON formatında yapılandırılır
   - Her gün için HTML ve PDF içerikleri ayrı ayrı sunulur

### URL Yapısı

- **HTML**: `https://resmigazete.gov.tr/DD.MM.YYYY`
- **PDF**: `https://www.resmigazete.gov.tr/eskiler/YYYY/MM/YYYYMMDD.pdf`

Örnek:
- HTML: `https://resmigazete.gov.tr/19.01.2026`
- PDF: `https://www.resmigazete.gov.tr/eskiler/2026/01/20260119.pdf`

## 🛠️ Kullanılan Teknolojiler

### Backend Framework
- **FastAPI**: Modern, hızlı web framework
- **Uvicorn**: ASGI server (FastAPI'yi çalıştırmak için)

### Web Scraping & API
- **Tavily API**: HTML içerik çekmek için web scraping servisi
- **Requests**: HTTP istekleri için

### PDF İşleme
- **PyPDF2**: PDF okuma ve metin çıkarma
- **pdf2image**: PDF sayfalarını görsele dönüştürme
- **Pillow (PIL)**: Görsel işleme

### OCR (Optik Karakter Tanıma)
- **pytesseract**: OCR motoru (Tesseract wrapper)
- Türkçe ve İngilizce dil desteği

### Yardımcı Kütüphaneler
- **python-dotenv**: Çevre değişkenleri yönetimi
- **datetime**: Tarih işlemleri

### Gereksinimler

```txt
fastapi
uvicorn
tavily-python
requests
PyPDF2
python-dotenv
pytesseract
pdf2image
Pillow
```

## 📦 Kurulum

### 1. Proje Dosyalarını İndirin

```bash
cd /home/ubuntu/elif-dev/denemev2
```

### 2. Sanal Ortam Oluşturun (Opsiyonel ama Önerilen)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Sistem Bağımlılıkları (OCR için)

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-tur poppler-utils
```

macOS:
```bash
brew install tesseract tesseract-lang poppler
```

### 5. Çevre Değişkenlerini Ayarlayın

`.env` dosyası oluşturun:

```bash
TAVILY_API_KEY=your_tavily_api_key_here
```

**Tavily API Key almak için**: [https://tavily.com](https://tavily.com)

## 🚀 Kullanım

### Sunucuyu Başlatma

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Parametreler:
- `--reload`: Kod değişikliklerinde otomatik yeniden başlatma
- `--host 0.0.0.0`: Tüm ağ arayüzlerinden erişim
- `--port 8000`: Sunucu portu

Sunucu başladığında:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### API Kullanımı

#### cURL ile Test

```bash
curl -X POST "http://localhost:8000/tools/resmi_gazete_getir" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2026-01-28",
    "end_date": "2026-01-29"
  }'
```

#### Python ile Kullanım

```python
import requests

url = "http://localhost:8000/tools/resmi_gazete_getir"
payload = {
    "start_date": "2026-01-28",
    "end_date": "2026-01-29"
}

response = requests.post(url, json=payload)
data = response.json()

print(data)
```

#### JavaScript/Node.js ile Kullanım

```javascript
const response = await fetch('http://localhost:8000/tools/resmi_gazete_getir', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    start_date: '2026-01-28',
    end_date: '2026-01-29'
  })
});

const data = await response.json();
console.log(data);
```

### Request Formatı

```json
{
  "start_date": "2026-01-19",
  "end_date": "2026-01-25"
}
```

**Parametreler:**
- `start_date`: Başlangıç tarihi (YYYY-MM-DD formatında)
- `end_date`: Bitiş tarihi (YYYY-MM-DD formatında)

### Response Formatı

```json
{
  "source": "resmi_gazete",
  "range": {
    "start": "2026-01-19",
    "end": "2026-01-25"
  },
  "days": [
    {
      "date": "2026-01-19",
      "html_url": "https://resmigazete.gov.tr/19.01.2026",
      "pdf_url": "https://www.resmigazete.gov.tr/eskiler/2026/01/20260119.pdf",
      "html_content": "HTML içeriği...",
      "pdf_content": "PDF'den çıkarılan metin içeriği..."
    },
    {
      "date": "2026-01-20",
      "html_url": "https://resmigazete.gov.tr/20.01.2026",
      "pdf_url": "https://www.resmigazete.gov.tr/eskiler/2026/01/20260120.pdf",
      "html_content": "HTML içeriği...",
      "pdf_content": "PDF'den çıkarılan metin içeriği..."
    }
  ]
}
```

## Özellikler

### Temel Özellikler

- ✅ Tarih aralığı bazlı veri çekme
- ✅ HTML ve PDF içerik desteği
- ✅ Otomatik OCR (taranmış PDF'ler için)
- ✅ Türkçe ve İngilizce metin tanıma
- ✅ Garbled text tespiti ve otomatik OCR'a geçiş
- ✅ Hata yönetimi ve retry mekanizması
- ✅ Timeout koruması (60 saniye)
- ✅ JSON formatında yapılandırılmış response
- ✅ MCP Tool standardına uyumluluk

### Güvenilirlik Özellikleri

- **Retry Mekanizması**: PDF indirme hatalarında 3 deneme
- **Timeout Koruması**: Uzun süren istekleri otomatik iptal
- **Hata Raporlama**: Detaylı hata mesajları
- **Garbled Text Tespiti**: Bozuk metin oranı kontrolü
- **Fallback OCR**: Text extraction başarısız olursa OCR devreye girer

## Mimari

### Sistem Akış Diyagramı

```
┌─────────────────┐
│   LLM/Client    │
└────────┬────────┘
         │
         │ HTTP POST Request
         │ {start_date, end_date}
         ▼
┌─────────────────────────────────────────┐
│        FastAPI MCP Server               │
│  ┌───────────────────────────────────┐  │
│  │   /tools/resmi_gazete_getir       │  │
│  └────────────┬──────────────────────┘  │
│               │                          │
│               ▼                          │
│  ┌────────────────────────┐             │
│  │  Date Range Calculator │             │
│  │  (start → end)         │             │
│  └────────────┬───────────┘             │
│               │                          │
│               ▼                          │
│  ┌────────────────────────┐             │
│  │  URL Builder           │             │
│  │  • HTML URL            │             │
│  │  • PDF URL             │             │
│  └────────────┬───────────┘             │
│               │                          │
│      ┌────────┴────────┐                │
│      ▼                 ▼                │
│  ┌───────┐      ┌──────────┐           │
│  │ Tavily│      │ PDF      │           │
│  │ API   │      │ Fetcher  │           │
│  │ (HTML)│      │          │           │
│  └───┬───┘      └────┬─────┘           │
│      │               │                  │
│      │               ▼                  │
│      │      ┌──────────────────┐       │
│      │      │  PyPDF2 Extract  │       │
│      │      └────┬────────┬────┘       │
│      │           │        │            │
│      │      Success?   Failure?        │
│      │           │        │            │
│      │           │        ▼            │
│      │           │  ┌──────────┐      │
│      │           │  │   OCR    │      │
│      │           │  │ (Tesseract│     │
│      │           │  │  +pdf2img)│     │
│      │           │  └────┬─────┘      │
│      │           │       │            │
│      └───────────┴───────┘            │
│                  │                     │
│                  ▼                     │
│      ┌─────────────────────┐          │
│      │  JSON Response      │          │
│      │  Builder            │          │
│      └──────────┬──────────┘          │
└─────────────────┼───────────────────┘
                  │
                  ▼
          ┌──────────────┐
          │   Response   │
          │   (JSON)     │
          └──────────────┘
```

### Veri Akışı

1. **İstek Alımı**: FastAPI endpoint'e POST request gelir
2. **Tarih Hesaplama**: start_date'ten end_date'e kadar günler hesaplanır
3. **Paralel İşleme**: Her gün için:
   - Tavily ile HTML içerik çekilir
   - PDF indirilip işlenir
4. **PDF İşleme Stratejisi**:
   - İlk olarak PyPDF2 ile metin çıkarımı denenir
   - Başarısız/garbled ise OCR devreye girer
5. **Sonuç Birleştirme**: Tüm günler için veriler JSON'da birleştirilir

### Dosya Yapısı

```
denemev2/
├── server.py              # Ana FastAPI uygulaması
├── tool_manifest.json     # MCP tool tanımlaması
├── .env                   # Çevre değişkenleri (API keys)
├── requirements.txt       # Python bağımlılıkları
└── README.md             # Bu dokümantasyon
```

## Yapılandırma

### Çevre Değişkenleri

| Değişken | Açıklama | Gerekli |
|----------|----------|---------|
| `TAVILY_API_KEY` | Tavily API anahtarı | ✅ Evet |

### Timeout Ayarları

`fetch_pdf` fonksiyonunda:
```python
timeout=60  # 60 saniye
max_retries=3  # 3 deneme
```

### OCR Dil Ayarları

```python
pytesseract.image_to_string(image, lang='tur+eng')
```

Desteklenen diller: Türkçe (`tur`) ve İngilizce (`eng`)

## Tool Manifest

`tool_manifest.json` dosyası, MCP protokolü için tool tanımını içerir:

```json
{
  "name": "resmi_gazete_getir",
  "description": "Belirtilen tarih aralığındaki Resmi Gazete HTML ve PDF içeriklerini Tavily kullanarak getirir",
  "method": "POST",
  "path": "/tools/resmi_gazete_getir",
  "input_schema": {
    "type": "object",
    "properties": {
      "start_date": {
        "type": "string",
        "format": "date",
        "description": "Başlangıç tarihi (YYYY-MM-DD)"
      },
      "end_date": {
        "type": "string",
        "format": "date",
        "description": "Bitiş tarihi (YYYY-MM-DD)"
      }
    },
    "required": ["start_date", "end_date"]
  }
}
```

## 🐛 Hata Yönetimi

Sistem şu hata senaryolarını yönetir:

1. **Tavily API Hataları**: HTML içerik çekilemezse hata mesajı döner
2. **PDF İndirme Hataları**: 3 deneme sonrası hata mesajı
3. **Timeout**: 60 saniye üzerinde süren istekler iptal edilir
4. **OCR Hataları**: OCR başarısız olursa hata mesajı döner
5. **Missing Dependencies**: Eksik kütüphaneler için uyarı mesajları

Örnek hata yanıtları:
```json
{
  "html_content": "HTML fetch error: Connection timeout",
  "pdf_content": "PDF fetch error: Max retries exceeded"
}
```

## Lisans

Bu proje için herhangi bir lisans belirtilmemiştir.


---

**Not**: Bu sistem bir MCP Tool Server'dır ve LLM'ler tarafından kullanılmak üzere tasarlanmıştır. Sistem kendi içinde LLM içermez.

