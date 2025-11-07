import os
import csv
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse

# === CONFIGURACIÓN ===
URL = "https://tecnocentercuba.com/products"
PROJECT_DIR = r"C:\Users\Arian\Documents\GitHub\cel"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
IMG_DIR = os.path.join(DATA_DIR, "images")

os.makedirs(IMG_DIR, exist_ok=True)

def download_image(img_url, filename):
    try:
        if not img_url or not img_url.startswith("http"):
            return ""
        resp = requests.get(img_url, timeout=10)
        resp.raise_for_status()
        with open(os.path.join(IMG_DIR, filename), "wb") as f:
            f.write(resp.content)
        return filename
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Imagen fallida: {e}")
        return ""

def main():
    print("🔄 Iniciando scraping con Selenium (esperando a que carguen los productos)...")

    # Configurar Chrome en modo headless (sin ventana)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

    # Usar webdriver-manager para no preocuparse por chromedriver
    from webdriver_manager.chrome import ChromeDriverManager
    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(URL)
        print("   🌐 Página abierta. Esperando a que carguen los productos...")

        # Esperar hasta 20 segundos a que aparezca al menos un producto
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card__title"))
        )
        print("   ✅ Productos detectados en la página.")

        # Extraer todos los productos del DOM
        product_elements = driver.find_elements(By.CSS_SELECTOR, ".product-view-handler")
        products = []

        for el in product_elements:
            try:
                title = el.find_element(By.CSS_SELECTOR, ".product-card__title").text.strip()
                if not title or title in ["Pasos para realizar un pedido", "Métodos de Pago", "Garantia de Moviles"]:
                    continue

                desc_elem = el.find_elements(By.CSS_SELECTOR, ".product-card__description")
                description = desc_elem[0].text.strip() if desc_elem else ""

                price_elem = el.find_elements(By.CSS_SELECTOR, ".product__price")
                price_text = price_elem[0].text.strip() if price_elem else "US$ 0.00"
                # Extraer número de "US$ 100.00"
                price_clean = ''.join(c for c in price_text if c.isdigit() or c == '.')
                price_base = float(price_clean) if price_clean else 0.0
                price_reseller = round(price_base + 5.0, 2)

                # Extraer URL de la imagen desde style="background-image: url(...)"
                img_url = ""
                img_containers = el.find_elements(By.CSS_SELECTOR, ".v-image__image--cover")
                if img_containers:
                    style = img_containers[0].get_attribute("style")
                    if "background-image: url(" in style:
                        start = style.find("url(") + 4
                        end = style.find(")", start)
                        if end != -1:
                            img_url = style[start:end].strip('"').strip("'")

                img_file = ""
                if img_url:
                    parsed = urlparse(img_url)
                    img_name = os.path.basename(parsed.path)
                    if not img_name or "." not in img_name:
                        safe = "".join(c for c in title if c.isalnum() or c in " _-")
                        img_name = f"{safe[:50]}.jpg"
                    img_file = download_image(img_url, img_name)

                products.append({
                    "title": title,
                    "description": description,
                    "price_base": price_base,
                    "price_reseller": price_reseller,
                    "price_currency": "USD",
                    "image_file": img_file,
                    "image_url": img_url,
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                continue  # Saltar productos mal formados

        # Guardar CSV
        csv_path = os.path.join(DATA_DIR, "products.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            if products:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)
                print(f"✅ Guardados {len(products)} productos en CSV.")
            else:
                f.write("title,description,price_base,price_reseller,price_currency,image_file,image_url,scraped_at\n")
                print("⚠️ No se extrajeron productos.")

    except Exception as e:
        print(f"🔥 Error con Selenium: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()