from fastapi import FastAPI
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from tavily import Client as TavilyClient
import requests
import io
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# --------------------
# Load .env
# --------------------
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY not found in .env")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

app = FastAPI(title="Resmi Gazete MCP Server")

# --------------------
# Helpers
# --------------------
def daterange(start_date: datetime, end_date: datetime):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

def build_urls(date: datetime):
    html_url = f"https://resmigazete.gov.tr/{date.strftime('%d.%m.%Y')}"
    pdf_url = (
        "https://www.resmigazete.gov.tr/eskiler/"
        f"{date.strftime('%Y')}/"
        f"{date.strftime('%m')}/"
        f"{date.strftime('%Y%m%d')}.pdf"
    )
    return html_url, pdf_url

def tavily_fetch(url: str):
    response = tavily_client.search(
        query=url,
        include_raw_content=True,
        max_results=1
    )
    if response.get("results"):
        return response["results"][0].get("raw_content")
    return None

def extract_text_with_ocr(pdf_bytes: bytes):
    """OCR kullanarak PDF'den metin çıkar (taranmış sayfalar için)"""
    if not OCR_AVAILABLE:
        return "OCR not available - pytesseract or pdf2image not installed"
    
    try:
        images = convert_from_bytes(pdf_bytes, dpi=300)
        text_content = []
        
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image, lang='tur+eng')
            text_content.append(f"--- Sayfa {i+1} (OCR) ---\n{text}")
        
        return "\n\n".join(text_content)
    except Exception as e:
        return f"OCR error: {str(e)}"

def is_text_garbled(text: str, threshold=0.3):
    """Metindeki garbled/bozuk karakter oranını kontrol et"""
    if not text or len(text) < 50:
        return False
    
    garbled_chars = sum(1 for c in text if ord(c) < 32 and c not in '\n\r\t')
    ratio = garbled_chars / len(text)
    return ratio > threshold

def fetch_pdf(url: str, max_retries=3):
    """PDF dosyasını indir ve text içeriğini çıkar (OCR desteği ile)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                timeout=60,
                headers=headers,
                stream=True
            )
            response.raise_for_status()
            
            pdf_content = response.content
            
            if PyPDF2 is None:
                return f"PDF downloaded ({len(pdf_content)} bytes) but PyPDF2 not installed for text extraction"
            
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            needs_ocr = False
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if not page_text.strip() or is_text_garbled(page_text):
                    needs_ocr = True
                    break
                
                text_content.append(page_text)
            
            if needs_ocr:
                print(f"📄 OCR gerekli: {url}")
                ocr_text = extract_text_with_ocr(pdf_content)
                return ocr_text
            
            full_text = "\n".join(text_content)
            return full_text if full_text.strip() else extract_text_with_ocr(pdf_content)
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue
            return f"PDF fetch error: Timeout after {max_retries} attempts"
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                continue
            return f"PDF fetch error: {str(e)}"
        except Exception as e:
            return f"PDF processing error: {str(e)}"
    
    return "PDF fetch error: Max retries exceeded"

# --------------------
# Tool Endpoint
# --------------------
@app.post("/tools/resmi_gazete_getir")
def resmi_gazete_getir(payload: dict):
    start = datetime.strptime(payload["start_date"], "%Y-%m-%d")
    end = datetime.strptime(payload["end_date"], "%Y-%m-%d")

    days = []

    for date in daterange(start, end):
        html_url, pdf_url = build_urls(date)

        day_data = {
            "date": date.strftime("%Y-%m-%d"),
            "html_url": html_url,
            "pdf_url": pdf_url,
            "html_content": None,
            "pdf_content": None
        }

        try:
            day_data["html_content"] = tavily_fetch(html_url)
        except Exception as e:
            day_data["html_content"] = f"HTML fetch error: {str(e)}"

        try:
            day_data["pdf_content"] = fetch_pdf(pdf_url)
        except Exception as e:
            day_data["pdf_content"] = f"PDF fetch error: {str(e)}"

        days.append(day_data)

    return {
        "source": "resmi_gazete",
        "range": {
            "start": payload["start_date"],
            "end": payload["end_date"]
        },
        "days": days
    }
