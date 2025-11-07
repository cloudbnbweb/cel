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

os.makedirs(IMAGES_FOLDER, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

manual_trigger = False

def wait_for_manual_trigger():
    global manual_trigger
    input("\n💡 Presiona ENTER para forzar una actualización manual.\n")
    manual_trigger = True

def download_image(img_url, filename):
    try:
        response = requests.get(img_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        with open(os.path.join(IMAGES_FOLDER, filename), 'wb') as f:
            f.write(response.content)
        return filename
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error descargando imagen {img_url}: {e}")
        return ""

def scrape_products_from_nuxt():
    print(f"[{datetime.now()}] 🔄 Descargando página y extrayendo productos desde window.__NUXT__...")
    response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    html = response.text

    # Buscar window.__NUXT__ = { ... }
    match = re.search(r'window\.__NUXT__\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not match:
        raise ValueError("❌ No se encontró window.__NUXT__ en el HTML.")

    try:
        nuxt_data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"❌ Error al parsear JSON de window.__NUXT__: {e}")

    # Buscar el array de productos en nuxt_data['fetch']
    products = []
    try:
        fetch_list = nuxt_data.get("fetch", [])
        for item in fetch_list:
            if isinstance(item, dict) and "data" in item:
                data = item["data"]
                if isinstance(data, list):
                    for entry in data:
                        if entry.get("@type") == "MenuItem":
                            products.append(entry)
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️ Error al navegar por nuxt_data: {e}")

    if not products:
        raise ValueError("❌ No se encontraron productos en window.__NUXT__.")

    # Procesar productos
    cleaned_products = []
    for p in products:
        name = p.get("name", "").strip()
        if not name or name in ["Pasos para realizar un pedido", "Métodos de Pago", "Garantia de Moviles"]:
            continue

        description = p.get("description", "").strip()
        image_url = p.get("image", "").strip()
        offers = p.get("offers", {})
        price = offers.get("price", 0)
        currency = offers.get("priceCurrency", "USD")

        try:
            price = float(price)
        except (TypeError, ValueError):
            price = 0.0

        price_reseller = round(price + 5.0, 2)

        img_filename = ""
        if image_url:
            parsed = urlparse(image_url)
            img_name = os.path.basename(parsed.path)
            if not img_name or "." not in img_name:
                safe_name = "".join(c for c in name if c.isalnum() or c in " _-")
                img_name = f"{safe_name[:50]}.jpg"
            img_filename = download_image(image_url, img_name)

        cleaned_products.append({
            "title": name,
            "description": description,
            "price_base": price,
            "price_reseller": price_reseller,
            "price_currency": currency,
            "image_file": img_filename,
            "image_url": image_url,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # Guardar CSV
    csv_path = os.path.join(DATA_FOLDER, "products.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if cleaned_products:
            writer = csv.DictWriter(f, fieldnames=cleaned_products[0].keys())
            writer.writeheader()
            writer.writerows(cleaned_products)
            print(f"[{datetime.now()}] ✅ Guardados {len(cleaned_products)} productos.")
        else:
            f.write("title,description,price_base,price_reseller,price_currency,image_file,image_url,scraped_at\n")
            print(f"[{datetime.now()}] ⚠️ No se encontraron productos válidos.")

def run_generate_html():
    print(f"[{datetime.now()}] 🖥️ Generando HTML estático...")
    try:
        result = subprocess.run(
            ["python", os.path.join(PROJECT_ROOT, "generate_html.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"[{datetime.now()}] ✅ HTML generado correctamente.")
        else:
            print(f"[{datetime.now()}] ❌ Error al generar HTML:\n{result.stderr}")
    except FileNotFoundError:
        print(f"[{datetime.now()}] ❌ No se encontró 'generate_html.py'")
    except Exception as e:
        print(f"[{datetime.now()}] 🔥 Excepción: {e}")

def git_commit_and_push():
    print(f"[{datetime.now()}] 🚀 Git: commit + push...")
    try:
        os.chdir(PROJECT_ROOT)
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("   ℹ️ Sin cambios.")
            return
        commit_msg = f"📦 Actualización de productos - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("   ✅ Push exitoso.")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Git error: {e}")

def run_full_cycle():
    try:
        scrape_products_from_nuxt()
        run_generate_html()
        git_commit_and_push()
    except Exception as e:
        print(f"[{datetime.now()}] 🔥 Error en ciclo: {e}")

def main():
    global manual_trigger
    print("🚀 Scraper para Tecno Center (usando window.__NUXT__)")
    print("🔁 Automático: cada 24h | ⌨️ Manual: presiona ENTER\n")

    input_thread = threading.Thread(target=wait_for_manual_trigger, daemon=True)
    input_thread.start()

    # Primera ejecución
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

        time.sleep(1)

if __name__ == "__main__":
    main()