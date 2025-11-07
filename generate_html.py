import os
import csv
from datetime import datetime

PROJECT_ROOT = r"C:\Users\Arian\Documents\GitHub\cel"
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")
OUTPUT_HTML = os.path.join(PROJECT_ROOT, "index.html")

def generate_html():
    csv_path = os.path.join(DATA_FOLDER, "products.csv")
    if not os.path.exists(csv_path):
        print("❌ No se encontró products.csv")
        return

    products = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["title"] and row["title"] != "Sin productos disponibles":
                products.append(row)

    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tecno Center - Mi MiniTienda</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: #f8f9fa;
            color: #212529;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
        }
        header h1 {
            font-size: 2.2rem;
            color: #006eff;
        }
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 25px;
        }
        .product-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transition: transform 0.2s;
        }
        .product-card:hover {
            transform: translateY(-5px);
        }
        .product-image {
            width: 100%;
            height: 200px;
            object-fit: contain;
            background: #f0f0f0;
            padding: 15px;
        }
        .product-info {
            padding: 16px;
        }
        .product-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #000;
        }
        .product-desc {
            font-size: 0.85rem;
            color: #555;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        .price-old {
            text-decoration: line-through;
            color: #888;
            font-size: 0.9rem;
        }
        .price-new {
            font-size: 1.3rem;
            font-weight: 600;
            color: #e74c3c;
            margin: 8px 0;
        }
        .btn-whatsapp {
            display: block;
            width: 100%;
            padding: 10px;
            background: #25d366;
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin-top: 10px;
            transition: background 0.3s;
        }
        .btn-whatsapp:hover {
            background: #1da851;
        }
        footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #777;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📦 Mi MiniTienda - Tecno Center</h1>
            <p>¿Interesado? Escríbeme por WhatsApp para reservar o más info.</p>
        </header>

        <div class="product-grid">
"""

    for p in products:
        img_src = f"data/images/{p['image_file']}" if p['image_file'] else "https://via.placeholder.com/280x200?text=Sin+imagen"
        base_price = f"{float(p['price_base']):.2f}" if p['price_base'] else "0.00"
        reseller_price = f"{float(p['price_reseller']):.2f}" if p['price_reseller'] else "5.00"

        # Reemplazar comillas para evitar romper el HTML
        title_safe = p['title'].replace('"', '&quot;')
        desc_safe = p['description'].replace('"', '&quot;').replace('\n', '<br>')

        html += f'''
            <div class="product-card">
                <img src="{img_src}" alt="{title_safe}" class="product-image">
                <div class="product-info">
                    <div class="product-title">{title_safe}</div>
                    <div class="product-desc">{desc_safe}</div>
                    <div class="price-old">Original: {base_price} USD</div>
                    <div class="price-new">👉 Revendedor: {reseller_price} USD</div>
                    <a href="https://wa.me/5351234567?text=Hola,%20estoy%20interesado%20en%20el%20producto:%20{title_safe.replace(" ", "%20")}" 
                       class="btn-whatsapp" target="_blank">
                        📩 Pedir por WhatsApp
                    </a>
                </div>
            </div>
        '''

    html += """
        </div>

        <footer>
            <p>© """ + datetime.now().strftime("%Y") + """ - Mi MiniTienda. Productos actualizados automáticamente desde Tecno Center.</p>
        </footer>
    </div>
</body>
</html>
"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Página HTML generada en {OUTPUT_HTML}")

if __name__ == "__main__":
    generate_html()