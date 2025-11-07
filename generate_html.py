import os
import csv

PROJECT_ROOT = r"C:\Users\Arian\Documents\GitHub\cel"
DATA_FOLDER = os.path.join(PROJECT_ROOT, "data")
OUTPUT_HTML = os.path.join(PROJECT_ROOT, "index.html")

def generate_html():
    csv_path = os.path.join(DATA_FOLDER, "products.csv")
    if not os.path.exists(csv_path):
        print("❌ No se encontró el archivo products.csv")
        return

    products = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)

    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mi MiniTienda - Revendedor</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f9f9f9; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
        .product-card { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 15px; text-align: center; }
        .product-card img { max-width: 100%; height: 180px; object-fit: contain; }
        .price { font-size: 1.2em; color: #e74c3c; font-weight: bold; margin: 10px 0; }
        .original { font-size: 0.9em; color: #777; text-decoration: line-through; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Mi MiniTienda - Productos Disponibles</h1>
        <div class="product-grid">
"""

    for p in products:
        img_src = f"data/images/{p['image_file']}" if p['image_file'] else "https://via.placeholder.com/250?text=Sin+imagen"
        html += f"""
            <div class="product-card">
                <img src="{img_src}" alt="{p['title']}">
                <h3>{p['title']}</h3>
                <div class="original">Original: {p['price_base']} USD</div>
                <div class="price">👉 Revendedor: {p['price_reseller']} USD</div>
            </div>
        """

    html += """
        </div>
    </div>
</body>
</html>
"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Página HTML generada en {OUTPUT_HTML}")

if __name__ == "__main__":
    generate_html()