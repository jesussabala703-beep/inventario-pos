from flask import Flask, render_template, request, jsonify
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
    return render_template('index.html')

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
        mensaje = "Producto registrado."
    except sqlite3.IntegrityError:
        mensaje = "El código ya existe."
    conn.close()
    return jsonify({'mensaje': mensaje})

@app.route('/procesar_venta', methods=['POST'])
def procesar_venta():
    data = request.json
    carrito = data['carrito']
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    total_venta = 0
    detalles_str = ""
    for item in carrito:
        subtotal = item['precio'] * item['cantidad']
        total_venta += subtotal
        detalles_str += f"{item['cantidad']}x {item['nombre']} (${item['precio']}), "
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE codigo = ?", (item['cantidad'], item['codigo']))
    
    cursor.execute("INSERT INTO ventas (total, detalles) VALUES (?, ?)", (total_venta, detalles_str))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'total': total_venta})

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    
