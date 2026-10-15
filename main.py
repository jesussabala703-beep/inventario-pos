from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total REAL NOT NULL,
            detalles TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Inventario y POS</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f4f9; margin: 0; padding: 20px; }
            .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            h2 { color: #333; }
            input, button { width: 100%%; padding: 10px; margin: 8px 0; box-sizing: border-box; }
            button { background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background: #218838; }
            .product-list { margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px; }
            .item { background: #f9f9f9; padding: 10px; margin-bottom: 5px; border-left: 4px solid #28a745; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📦 Sistema de Caja e Inventario</h2>
            <h3>Registrar Producto</h3>
            <input type="text" id="codigo" placeholder="Código del producto">
            <input type="text" id="nombre" placeholder="Nombre del producto">
            <input type="number" id="precio" placeholder="Precio ($)" step="0.01">
            <input type="number" id="cantidad" placeholder="Cantidad / Stock">
            <button onclick="guardarProducto()">Guardar en Inventario</button>

            <div class="product-list">
                <h3>Inventario Actual</h3>
                <div id="lista-productos">Cargando productos...</div>
            </div>
        </div>

        <script>
            async function cargarProductos() {
                const res = await fetch('/productos');
                const productos = await res.json();
                const contenedor = document.getElementById('lista-productos');
                if(productos.length === 0) {
                    contenedor.innerHTML = '<p>No hay productos registrados.</p>';
                    return;
                }
                contenedor.innerHTML = productos.map(p => 
                    `<div class="item"><b>${p[1]}</b> - ${p[2]} | Precio: $${p[3]} | Stock: ${p[4]}</div>`
                ).join('');
            }

            async function guardarProducto() {
                const codigo = document.getElementById('codigo').value;
                const nombre = document.getElementById('nombre').value;
                const precio = parseFloat(document.getElementById('precio').value);
                const cantidad = parseInt(document.getElementById('cantidad').value);

                if(!codigo || !nombre || isNaN(precio) || isNaN(cantidad)) {
                    alert('Por favor completa todos los campos correctamente.');
                    return;
                }

                const res = await fetch('/agregar_producto', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({codigo, nombre, precio, cantidad})
                });
                const data = await res.json();
                alert(data.mensaje);
                document.getElementById('codigo').value = '';
                document.getElementById('nombre').value = '';
                document.getElementById('precio').value = '';
                document.getElementById('cantidad').value = '';
                cargarProductos();
            }

            cargarProductos();
        </script>
    </body>
    </html>
    '''

@app.route('/productos', methods=['GET'])
def obtener_productos():
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, nombre, precio, stock FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return jsonify(productos)

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    data = request.json
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO productos (codigo, nombre, precio, stock) VALUES (?, ?, ?, ?)",
                       (data['codigo'], data['nombre'], data['precio'], data['cantidad']))
        conn.commit()
        mensaje = "Producto registrado con éxito."
    except sqlite3.IntegrityError:
        mensaje = "El código ya existe."
    conn.close()
    return jsonify({'mensaje': mensaje})

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
