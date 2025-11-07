import os
import csv
import json
import time
import subprocess
import requests
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

# === FUNCIONES ===

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

def scrape_products_from_jsonld():
    print(f"[{datetime.now()}] 🔄 Obteniendo productos desde JSON-LD...")
    response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    html = response.text

    start = html.find('<script type="application/ld+json">')
    if start == -1:
        raise ValueError("❌ No se encontró el bloque JSON-LD.")

    start += len('<script type="application/ld+json">')
    end = html.find('</script>', start)
    if end == -1:
        raise ValueError("❌ El bloque JSON-LD está mal formado.")

    json_text = html[start:end].strip()
    data = json.loads(json_text)

    menu_sections = data.get("hasMenuSection", [])
    products = []

    for section in menu_sections:
        menu_items = section.get("hasMenuItem", [])
        for item in menu_items:
            if item.get("@type") != "MenuItem":
                continue

            name = item.get("name", "").strip()
            if not name or name in ["Pasos para realizar un pedido", "Métodos de Pago"]:
                continue

            description = item.get("description", "").strip()
            image_url = item.get("image", "").strip()
            offers = item.get("offers", {})
            price = offers.get("price")
            currency = offers.get("priceCurrency", "USD")

            try:
                price = float(price)
            except (TypeError, ValueError):
                price = 0.0

            price_reseller = round(price + 5.0, 2)

            img_filename = ""
            if image_url:
                img_name = os.path.basename(urlparse(image_url).path)
                if not img_name or "." not in img_name:
                    img_name = f"{name.replace(' ', '_').replace('/', '_')}.jpg"
                img_filename = download_image(image_url, img_name)

            products.append({
                "title": name,
                "description": description,
                "price_base": price,
                "price_reseller": price_reseller,
                "price_currency": currency,
                "image_file": img_filename,
                "image_url": image_url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    csv_path = os.path.join(DATA_FOLDER, "products.csv")
    if products:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=products[0].keys())
            writer.writeheader()
            writer.writerows(products)
        print(f"[{datetime.now()}] ✅ Guardados {len(products)} productos.")
    else:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("title,description,price_base,price_reseller,price_currency,image_file,image_url,scraped_at\n")
        print(f"[{datetime.now()}] ⚠️ No se encontraron productos.")

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
        print(f"[{datetime.now()}] 🔥 Excepción al ejecutar generate_html.py: {e}")

def git_commit_and_push():
    print(f"[{datetime.now()}] 🚀 Haciendo commit y push a GitHub...")
    try:
        os.chdir(PROJECT_ROOT)

        # Agregar cambios
        subprocess.run(["git", "add", "."], check=True)

        # Verificar si hay cambios para commitear
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print(f"[{datetime.now()}] ℹ️ No hay cambios nuevos para commitear.")
            return

        # Hacer commit
        commit_msg = f"Actualización automática de productos - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        # Hacer push
        subprocess.run(["git", "push"], check=True)

        print(f"[{datetime.now()}] ✅ Push realizado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] ❌ Error en Git:\n{e}")
    except Exception as e:
        print(f"[{datetime.now()}] 🔥 Error inesperado en Git: {e}")

# === BUCLE PRINCIPAL ===
def main():
    print("🚀 Scraper + Publicador automático para Tecno Center")
    print("🔁 Ciclo: scrape → generate_html → git push (cada 24h)")
    while True:
        try:
            scrape_products_from_jsonld()
            run_generate_html()
            git_commit_and_push()
        except Exception as e:
            print(f"[{datetime.now()}] 🔥 Error en el ciclo principal: {e}")

        print(f"[{datetime.now()}] ⏳ Esperando 24 horas para la próxima actualización...\n")
        time.sleep(24 * 60 * 60)

if __name__ == "__main__":
    main()