import os
import requests
from datetime import datetime

# Configuración
URL = "https://tecnocentercuba.com/products"
PROJECT_ROOT = r"C:\Users\Arian\Documents\GitHub\cel"
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "pagina_tecno_center.html")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def descargar_html():
    print(f"[{datetime.now()}] 🌐 Descargando contenido de {URL}...")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"[{datetime.now()}] ✅ HTML guardado en: {OUTPUT_FILE}")
        print(f"📄 Tamaño del archivo: {len(response.text)} caracteres")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error al descargar la página: {e}")

if __name__ == "__main__":
    descargar_html()