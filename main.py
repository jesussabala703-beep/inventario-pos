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
        <title>Sistema de Caja e Inventario Rápido</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f4f9; margin: 0; padding: 15px; }
            .container { max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            h2, h3 { color: #333; }
            input, button { width: 100%; padding: 10px; margin: 6px 0; box-sizing: border-box; }
            button { background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; }
            button:hover { background: #0056b3; }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #218838; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #c82333; }
            .row { display: flex; flex-wrap: wrap; gap: 20px; }
            .col { flex: 1; min-width: 280px; background: #fdfdfd; padding: 15px; border: 1px solid #ddd; border-radius: 6px; }
            .item-list, .cart-list { margin-top: 10px; max-height: 200px; overflow-y: auto; border: 1px solid #eee; padding: 8px; display: none; }
            .item { background: #fff; padding: 8px; margin-bottom: 5px; border-left: 4px solid #007bff; display: flex; justify-content: space-between; align-items: center; }
            .cart-item { background: #fff; padding: 6px; margin-bottom: 4px; border-left: 4px solid #28a745; font-size: 14px; display: flex; justify-content: space-between; }
            .shortcuts-info { font-size: 12px; color: #666; background: #f1f1f1; padding: 8px; border-radius: 4px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🛒 Sistema de Caja e Inventario Rápido</h2>
            
            <div class="row">
                <!-- Columna Izquierda: Inventario y Registro -->
                <div class="col">
                    <h3>🔍 Buscar Producto</h3>
                    <input type="text" id="busqueda" placeholder="Escribe el nombre o código..." onkeyup="filtrarProductos()">
                    
                    <div class="item-list" id="lista-productos">
                        <p>Escribe algo para buscar...</p>
                    </div>

                    <div class="shortcuts-info">
                        <b>Atajos de Teclado:</b><br>
                        [F1] Mostrar todo | [F2] Limpiar búsqueda<br>
                        [F3] Cobrar factura | [F4] Cancelar carrito
                    </div>

                    <h3 style="margin-top:20px;">➕ Registrar Producto Nuevo</h3>
                    <input type="text" id="reg-codigo" placeholder="Código">
                    <input type="text" id="reg-nombre" placeholder="Nombre">
                    <input type="number" id="reg-precio" placeholder="Precio ($)" step="0.01">
                    <input type="number" id="reg-cantidad" placeholder="Cantidad / Stock">
                    <button class="btn-success" onclick="guardarProducto()">Guardar en Inventario</button>
                </div>

                <!-- Columna Derecha: Carrito y Facturación -->
                <div class="col">
                    <h3>🛍️ Carrito de Venta</h3>
                    <div class="cart-list" id="lista-carrito" style="display: block;">
                        <p>El carrito está vacío.</p>
                    </div>
                    <h3 style="margin-top:15px;">Total: $<span id="total-venta">0.00</span></h3>
                    <button class="btn-success" onclick="procesarVenta()">🖨️ Cobrar y Generar Factura [F3]</button>
                    <button class="btn-danger" onclick="cancelarCarrito()" style="margin-top: 5px;">❌ Cancelar Compra [F4]</button>
                </div>
            </div>
        </div>

        <script>
            let inventarioGlobal = [];
            let carrito = [];

            async function cargarProductos() {
                const res = await fetch('/productos');
                inventarioGlobal = await res.json();
            }

            function mostrarInventario(productos, forzarVisible = false) {
                const contenedor = document.getElementById('lista-productos');
                const textoBusqueda = document.getElementById('busqueda').value.trim();

                if (textoBusqueda === '' && !forzarVisible) {
                    contenedor.style.display = 'none';
                    return;
                }

                contenedor.style.display = 'block';
                if(productos.length === 0) {
                    contenedor.innerHTML = '<p>No se encontraron productos.</p>';
                    return;
                }
                contenedor.innerHTML = productos.map(p => `
                    <div class="item">
                        <div><b>${p[1]}</b> - ${p[2]}<br><small>Precio: $${p[3]} | Stock: ${p[4]}</small></div>
                        <button onclick="agregarAlCarrito(${p[0]}, '${p[1]}', '${p[2]}', ${p[3]}, ${p[4]})" style="width:auto; padding:5px 10px;">Agregar</button>
                    </div>
                `).join('');
            }

            function filtrarProductos() {
                const texto = document.getElementById('busqueda').value.toLowerCase().trim();
                if(texto === '') {
                    document.getElementById('lista-productos').style.display = 'none';
                    return;
                }
                // Búsqueda inteligente por coincidencia parcial en nombre o código
                const filtrados = inventarioGlobal.filter(p => p[1].toLowerCase().includes(texto) || p[2].toLowerCase().includes(texto));
                mostrarInventario(filtrados);
            }

            function limpiarBusqueda() {
                document.getElementById('busqueda').value = '';
                document.getElementById('lista-productos').style.display = 'none';
            }

            function cancelarCarrito() {
                if(carrito.length === 0) return;
                if(confirm('¿Estás seguro de cancelar la compra actual?')) {
                    carrito = [];
                    actualizarCarrito();
                }
            }

            async function guardarProducto() {
                const codigo = document.getElementById('reg-codigo').value;
                const nombre = document.getElementById('reg-nombre').value;
                const precio = parseFloat(document.getElementById('reg-precio').value);
                const cantidad = parseInt(document.getElementById('reg-cantidad').value);

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
                
                document.getElementById('reg-codigo').value = '';
                document.getElementById('reg-nombre').value = '';
                document.getElementById('reg-precio').value = '';
                document.getElementById('reg-cantidad').value = '';
                cargarProductos();
            }

            function agregarAlCarrito(id, codigo, nombre, precio, stockMax) {
                let itemEnCarrito = carrito.find(i => i.id === id);
                if(itemEnCarrito) {
                    if(itemEnCarrito.cantidad < stockMax) {
                        itemEnCarrito.cantidad++;
                    } else {
                        alert('No hay más stock disponible.');
                        return;
                    }
                } else {
                    if(stockMax > 0) {
                        carrito.push({id, codigo, nombre, precio, cantidad: 1});
                    } else {
                        alert('Producto sin stock.');
                        return;
                    }
                }
                actualizarCarrito();
            }

            function actualizarCarrito() {
                const contenedor = document.getElementById('lista-carrito');
                if(carrito.length === 0) {
                    contenedor.innerHTML = '<p>El carrito está vacío.</p>';
                    document.getElementById('total-venta').innerText = '0.00';
                    return;
                }

                let total = 0;
                contenedor.innerHTML = carrito.map(i => {
                    let subtotal = i.precio * i.cantidad;
                    total += subtotal;
                    return `<div class="cart-item">
                        <span><b>${i.nombre}</b> x${i.cantidad}</span>
                        <span>$${subtotal.toFixed(2)}</span>
                    </div>`;
                }).join('');

                document.getElementById('total-venta').innerText = total.toFixed(2);
            }

            async function procesarVenta() {
                if(carrito.length === 0) {
                    alert('El carrito está vacío.');
                    return;
                }

                const res = await fetch('/procesar_venta', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({carrito})
                });
                const data = await res.json();
                
                if(data.success) {
                    alert('¡Venta procesada con éxito! Total a pagar: $' + data.total.toFixed(2));
                    carrito = [];
                    actualizarCarrito();
                    cargarProductos();
                } else {
                    alert('Error al procesar la venta.');
                }
            }

            // Manejo de Atajos de Teclado (F1, F2, F3, F4)
            window.addEventListener('keydown', function(e) {
                if (e.key === 'F1') {
                    e.preventDefault();
                    mostrarInventario(inventarioGlobal, true);
                } else if (e.key === 'F2') {
                    e.preventDefault();
                    limpiarBusqueda();
                } else if (e.key === 'F3') {
                    e.preventDefault();
                    procesarVenta();
                } else if (e.key === 'F4') {
                    e.preventDefault();
                    cancelarCarrito();
                }
            });

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
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (item['cantidad'], item['id']))
    
    cursor.execute("INSERT INTO ventas (total, detalles) VALUES (?, ?)", (total_venta, detalles_str))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'total': total_venta})

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
