import os
import csv
import json
import time
import threading
import subprocess
import requests
from urllib.parse import urlparse
from datetime import datetime

# === CONFIGURACIÓN ===
API_URL = "https://api.olaclick.app/api/v1/companies/tecnocentercuba/products"
PROJECT_ROOT = r"C:\Users\Arian\Documents\GitHub\cel"
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")
IMAGES_FOLDER = os.path.join(DATA_FOLDER, "images")
DEBUG_JSON = os.path.join(PROJECT_ROOT, "debug_api.json")

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
        print("\n⚠️ Input no disponible. Continuando en modo automático.")
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

def scrape_from_api():
    print(f"[{datetime.now()}] 🌐 Consultando API oficial de Tecno Center...")
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Guardar para debugging
        with open(DEBUG_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"   💾 Respuesta de API guardada en: {DEBUG_JSON}")

        products = []
        for item in data.get("data", []):
            name = item.get("name", "").strip()
            if not name or name in ["Pasos para realizar un pedido", "Métodos de Pago", "Garantia de Moviles"]:
                continue

            description = item.get("description", "").strip()
            image_url = item.get("image_thumbnail_url", "") or item.get("image_url", "")
            price = item.get("price", 0)
            currency = "USD"

            price_reseller = round(float(price) + 5.0, 2)

            img_file = ""
            if image_url:
                parsed = urlparse(image_url)
                img_name = os.path.basename(parsed.path)
                if not img_name or "." not in img_name:
                    safe = "".join(c for c in name if c.isalnum() or c in " _-")
                    img_name = f"{safe[:50]}.jpg"
                img_file = download_image(image_url, img_name)

            products.append({
                "title": name,
                "description": description,
                "price_base": price,
                "price_reseller": price_reseller,
                "price_currency": currency,
                "image_file": img_file,
                "image_url": image_url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # Guardar CSV
        csv_path = os.path.join(DATA_FOLDER, "products.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            if products:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)
                print(f"[{datetime.now()}] ✅ Guardados {len(products)} productos.")
            else:
                f.write("title,description,price_base,price_reseller,price_currency,image_file,image_url,scraped_at\n")
                print(f"[{datetime.now()}] ⚠️ No se encontraron productos válidos.")

    except Exception as e:
        print(f"[{datetime.now()}] 🔥 Error al consultar la API: {e}")

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
        print(f"[{datetime.now()}] 🔥 Excepción: {e}")

def git_commit_and_push():
    print(f"[{datetime.now()}] 🚀 Git: commit + push...")
    try:
        os.chdir(PROJECT_ROOT)
        subprocess.run(["git", "add", "."], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("   ℹ️ Sin cambios.")
            return
        commit_msg = f"📦 Actualización de productos - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "push"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   ✅ Push exitoso.")
    except FileNotFoundError:
        print("   ❌ 'git' no encontrado. Instala Git y agrégalo al PATH.")
    except Exception as e:
        print(f"   ❌ Error en Git: {e}")

def run_full_cycle():
    scrape_from_api()
    run_generate_html()
    git_commit_and_push()

def main():
    global manual_trigger
    print("🚀 Scraper para Tecno Center (usando API oficial de OlaClick)")
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