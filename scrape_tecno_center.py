import os
import csv
import json
import time
import threading
import subprocess
import requests
import re
from urllib.parse import urlparse
from datetime import datetime

# === CONFIGURACIÓN ===
BASE_URL = "https://tecnocentercuba.com/products"
PROJECT_ROOT = r"C:\Users\Arian\Documents\GitHub\cel"
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")
IMAGES_FOLDER = os.path.join(DATA_FOLDER, "images")
DEBUG_HTML = os.path.join(PROJECT_ROOT, "debug.html")

os.makedirs(IMAGES_FOLDER, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

manual_trigger = False

def wait_for_manual_trigger():
    global manual_trigger
    try:
        input("\n💡 Presiona ENTER para forzar una actualización manual.\n")
        manual_trigger = True
    except EOFError:
        print("\n⚠️ Input no disponible. Esperando en modo automático.")
        time.sleep(3600)
        threading.Thread(target=wait_for_manual_trigger, daemon=True).start()

def download_image(img_url, filename):
    try:
        if not img_url or not img_url.startswith("http"):
            return ""
        response = requests.get(img_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        with open(os.path.join(IMAGES_FOLDER, filename), 'wb') as f:
            f.write(response.content)
        return filename
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error descargando imagen {img_url}: {e}")
        return ""

def extract_products_from_html(html_content):
    print(f"[{datetime.now()}] 🔍 Buscando JSON-LD en el HTML...")
    # Buscar el bloque exacto que contiene los productos
    pattern = r'<script[^>]*data-hid="products-ld-json-schema"[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
    match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        # Intentar fallback: cualquier script con type=application/ld+json
        pattern_fallback = r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        match = re.search(pattern_fallback, html_content, re.DOTALL | re.IGNORECASE)

    if not match:
        raise ValueError("❌ No se encontró ningún bloque JSON-LD en el HTML.")

    try:
        json_text = match.group(1).strip()
        data = json.loads(json_text)
        menu_sections = data.get("hasMenuSection", [])
        products = []
        for section in menu_sections:
            for item in section.get("hasMenuItem", []):
                if item.get("@type") == "MenuItem":
                    products.append(item)
        if not products:
            raise ValueError("⚠️ JSON-LD encontrado, pero sin productos.")
        print(f"   ✅ Encontrados {len(products)} productos.")
        return products
    except json.JSONDecodeError as e:
        raise ValueError(f"❌ Error al parsear JSON-LD: {e}")

def scrape_and_save():
    print(f"[{datetime.now()}] 🌐 Descargando página desde {BASE_URL}...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html_content = response.text

        with open(DEBUG_HTML, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"   💾 HTML guardado en: {DEBUG_HTML}")

        products = extract_products_from_html(html_content)

        # Filtrar entradas no deseadas
        cleaned = []
        skip_names = {"Pasos para realizar un pedido", "Métodos de Pago", "Garantia de Moviles", "Whatsapp Gestor 1", "Whatsapp Gestor 2"}
        for p in products:
            name = p.get("name", "").strip()
            if not name or name in skip_names:
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

            cleaned.append({
                "title": name,
                "description": desc,
                "price_base": price,
                "price_reseller": price_reseller,
                "price_currency": currency,
                "image_file": img_file,
                "image_url": img_url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        csv_path = os.path.join(DATA_FOLDER, "products.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            if cleaned:
                writer = csv.DictWriter(f, fieldnames=cleaned[0].keys())
                writer.writeheader()
                writer.writerows(cleaned)
                print(f"[{datetime.now()}] ✅ Guardados {len(cleaned)} productos en CSV.")
            else:
                f.write("title,description,price_base,price_reseller,price_currency,image_file,image_url,scraped_at\n")
                print(f"[{datetime.now()}] ⚠️ No se encontraron productos válidos.")

    except Exception as e:
        print(f"[{datetime.now()}] 🔥 Error al scrapear: {e}")

def run_generate_html():
    print(f"[{datetime.now()}] 🖥️ Generando HTML estático...")
    try:
        result = subprocess.run(
            ["python", os.path.join(PROJECT_ROOT, "generate_html.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30
        )
        if result.returncode == 0:
            print(f"[{datetime.now()}] [OK] HTML generado correctamente.")
        else:
            print(f"[{datetime.now()}] [ERROR] generate_html.py:\n{result.stderr}")
    except Exception as e:
        print(f"[{datetime.now()}] 🔥 Excepción en generate_html.py: {e}")

def git_commit_and_push():
    print(f"[{datetime.now()}] 🚀 Git: commit + push...")
    try:
        os.chdir(PROJECT_ROOT)
        subprocess.run(["git", "add", "."], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("   ℹ️ Sin cambios nuevos.")
            return
        commit_msg = f"📦 Actualización de productos - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "push"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   ✅ Push exitoso.")
    except FileNotFoundError:
        print("   ❌ 'git' no encontrado. Instálalo y agrégalo al PATH.")
    except Exception as e:
        print(f"   ❌ Error en Git: {e}")

def run_full_cycle():
    scrape_and_save()
    run_generate_html()
    git_commit_and_push()

def main():
    global manual_trigger
    print("🚀 Scraper para Tecno Center (usando JSON-LD desde debug.html)")
    print("🔁 Automático: cada 24h | ⌨️ Manual: presiona ENTER\n")

    input_thread = threading.Thread(target=wait_for_manual_trigger, daemon=True)
    input_thread.start()

    run_full_cycle()
    next_auto = time.time() + 24 * 3600

    while True:
        if manual_trigger:
            print("\n✅ Actualización manual forzada.")
            run_full_cycle()
            next_auto = time.time() + 24 * 3600
            manual_trigger = False
            input_thread = threading.Thread(target=wait_for_manual_trigger, daemon=True)
            input_thread.start()

        if time.time() >= next_auto:
            print("\n⏰ Actualización automática programada.")
            run_full_cycle()
            next_auto = time.time() + 24 * 3600

        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] 🛑 Detenido por el usuario.")