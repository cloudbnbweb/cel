import os
import csv
import json
import time
import requests
import re
from urllib.parse import urlparse
from datetime import datetime

URL = "https://tecnocentercuba.com/products"
PROJECT_DIR = r"C:\Users\Arian\Documents\GitHub\cel"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
IMG_DIR = os.path.join(DATA_DIR, "images")
DEBUG_HTML = os.path.join(PROJECT_DIR, "debug.html")

os.makedirs(IMG_DIR, exist_ok=True)

# Lista de User-Agents realistas
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]

def download_image(url, filename):
    try:
        if not url or not url.startswith("http"):
            return ""
        resp = requests.get(url, headers={"User-Agent": USER_AGENTS[0]}, timeout=10)
        resp.raise_for_status()
        with open(os.path.join(IMG_DIR, filename), "wb") as f:
            f.write(resp.content)
        return filename
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Imagen fallida: {e}")
        return ""

def extract_from_jsonld(html):
    # Buscar cualquier script con type=application/ld+json
    matches = re.findall(
        r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE
    )
    for block in matches:
        try:
            data = json.loads(block.strip())
            if isinstance(data, dict) and data.get("@type") == "Menu" and "hasMenuSection" in 
                products = []
                for section in data.get("hasMenuSection", []):
                    for item in section.get("hasMenuItem", []):
                        if item.get("@type") == "MenuItem":
                            products.append(item)
                if products:
                    return products
        except json.JSONDecodeError:
            continue
    return None

def main():
    print("🔄 Scraping de Tecno Center desde JSON-LD (con reintentos)...")
    
    for attempt in range(3):
        ua = USER_AGENTS[attempt % len(USER_AGENTS)]
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            print(f"   Intento {attempt + 1}/3 con User-Agent: {ua[:50]}...")
            resp = requests.get(URL, headers=headers, timeout=15)
            resp.raise_for_status()
            html = resp.text

            with open(DEBUG_HTML, "w", encoding="utf-8") as f:
                f.write(html)

            products = extract_from_jsonld(html)
            if products:
                print(f"   ✅ Encontrados {len(products)} productos.")
                break
            else:
                print("   ⚠️ No se encontró JSON-LD válido.")
                time.sleep(2)
        except Exception as e:
            print(f"   ❌ Error en intento {attempt + 1}: {e}")
            time.sleep(3)
    else:
        print("   🔥 Fallaron todos los intentos. Guardando CSV vacío.")
        with open(os.path.join(DATA_DIR, "products.csv"), "w", encoding="utf-8") as f:
            f.write("title,description,price_base,price_reseller,price_currency,image_file,image_url,scraped_at\n")
        return

    # Filtrar productos no deseados
    skip = {"Pasos para realizar un pedido", "Métodos de Pago", "Garantia de Moviles", "Whatsapp Gestor"}
    valid = []
    for p in products:
        name = p.get("name", "").strip()
        if not name or any(s in name for s in skip):
            continue

        desc = p.get("description", "").strip()
        img_url = p.get("image", "").strip()
        offers = p.get("offers", {})
        price = offers.get("price", 0)
        currency = offers.get("priceCurrency", "USD")

        try:
            price = float(price)
        except (TypeError, ValueError):
            price = 0.0

        price_reseller = round(price + 5.0, 2)

        img_file = ""
        if img_url:
            parsed = urlparse(img_url)
            img_name = os.path.basename(parsed.path)
            if not img_name or "." not in img_name:
                safe = "".join(c for c in name if c.isalnum() or c in " _-")
                img_name = f"{safe[:50]}.jpg"
            img_file = download_image(img_url, img_name)

        valid.append({
            "title": name,
            "description": desc,
            "price_base": price,
            "price_reseller": price_reseller,
            "price_currency": currency,
            "image_file": img_file,
            "image_url": img_url,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # Guardar CSV
    csv_path = os.path.join(DATA_DIR, "products.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if valid:
            writer = csv.DictWriter(f, fieldnames=valid[0].keys())
            writer.writeheader()
            writer.writerows(valid)
            print(f"✅ Guardado: {len(valid)} productos.")
        else:
            f.write("title,description,price_base,price_reseller,price_currency,image_file,image_url,scraped_at\n")
            print("⚠️ Ningún producto válido.")

if __name__ == "__main__":
    main()