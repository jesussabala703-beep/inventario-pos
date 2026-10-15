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
            .container { max-width: 950px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); position: relative; }
            h2, h3 { color: #333; margin-top: 0; }
            input, button { width: 100%; padding: 10px; margin: 6px 0; box-sizing: border-box; }
            button { background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
            button:hover { background: #0056b3; }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #218838; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #c82333; }
            .btn-warning { background: #ffc107; color: #333; font-weight: bold; }
            .btn-warning:hover { background: #e0a800; }
            .row { display: flex; flex-wrap: wrap; gap: 20px; }
            .col { flex: 1; min-width: 280px; background: #fdfdfd; padding: 15px; border: 1px solid #ddd; border-radius: 6px; }
            .item-list, .cart-list { margin-top: 10px; max-height: 200px; overflow-y: auto; border: 1px solid #eee; padding: 8px; display: none; }
            .item { background: #fff; padding: 8px; margin-bottom: 6px; border-left: 4px solid #007bff; display: flex; justify-content: space-between; align-items: center; }
            .cart-item { background: #fff; padding: 6px; margin-bottom: 4px; border-left: 4px solid #28a745; font-size: 14px; display: flex; justify-content: space-between; }
            
            /* Recuadro Tasa BCV */
            .bcv-box { position: absolute; top: 20px; right: 20px; background: #e8f5e9; border: 1px solid #c8e6c9; padding: 8px 12px; border-radius: 6px; text-align: right; font-size: 13px; color: #2e7d32; }
            .bcv-box input { width: 80px; padding: 3px; text-align: center; font-weight: bold; margin-left: 5px; }

            /* Modal de Inventario Completo */
            .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
            .modal-content { background: white; margin: 10% auto; padding: 20px; width: 90%; max-width: 600px; border-radius: 8px; max-height: 70vh; overflow-y: auto; }
            .close-modal { float: right; background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Recuadro Tasa BCV -->
            <div class="bcv-box">
                <b> tasa BCV:</b> <input type="number" id="tasa-bcv" value="36.50" step="0.01" onchange="actualizarCalculos()"> Bs/$
            </div>

            <h2>🛒 Sistema de Caja e Inventario Rápido</h2>
            
            <div class="row">
                <!-- Columna Izquierda: Búsqueda y Registro -->
                <div class="col">
                    <h3>🔍 Buscar Producto</h3>
                    <input type="text" id="busqueda" placeholder="Ej. bujía, freno, manubrio..." onkeyup="filtrarProductos()">
                    
                    <div style="display: flex; gap: 5px; margin-top: 5px;">
                        <button class="btn-warning" onclick="abrirModalInventario()">📦 Ver Stock [F1]</button>
                        <button class="btn-warning" onclick="cerrarTodo()">❌ Limpiar [F2]</button>
                    </div>

                    <div class="item-list" id="lista-productos"></div>

                    <h3 style="margin-top:20px;">➕ Registrar Producto Nuevo</h3>
                    <input type="text" id="reg-codigo" placeholder="Código">
                    <input type="text" id="reg-nombre" placeholder="Nombre (Ej. Bujía Racing)">
                    <input type="number" id="reg-precio" placeholder="Precio ($)" step="0.01">
                    <input type="number" id="reg-cantidad" placeholder="Cantidad / Stock Inicial">
                    <button class="btn-success" onclick="guardarProducto()">Guardar en Inventario</button>
                </div>

                <!-- Columna Derecha: Carrito y Facturación -->
                <div class="col">
                    <h3>🛍️ Carrito de Venta</h3>
                    <div class="cart-list" id="lista-carrito" style="display: block;">
                        <p>El carrito está vacío.</p>
                    </div>
                    <h3 style="margin-top:15px;">
                        Total: $<span id="total-dolar">0.00</span><br>
                        <small style="color: #007bff;">Bs. <span id="total-bs">0.00</span></small>
                    </h3>
                    
                    <button class="btn-success" onclick="procesarVenta()">🖨️ Cobrar / Facturar [Ctrl+3]</button>
                    <button class="btn-danger" onclick="cancelarCarrito()" style="margin-top: 5px;">❌ Cancelar Compra [Ctrl+4]</button>
                </div>
            </div>
        </div>

        <!-- Modal de Inventario Completo y Reposición de Stock -->
        <div id="modal-inventario" class="modal">
            <div class="modal-content">
                <button class="close-modal" onclick="cerrarModalInventario()">Cerrar [F2]</button>
                <h3>📦 Inventario Completo y Reposición de Stock</h3>
                <div id="contenido-modal-stock">Cargando...</div>
            </div>
        </div>

        <script>
            let inventarioGlobal = [];
            let carrito = [];

            async function cargarProductos() {
                const res = await fetch('/productos');
                inventarioGlobal = await res.json();
                if(document.getElementById('modal-inventario').style.display === 'block') {
                    renderizarStockModal();
                }
            }

            function filtrarProductos() {
                const texto = document.getElementById('busqueda').value.toLowerCase().trim();
                const contenedor = document.getElementById('lista-productos');
                if(texto === '') {
                    contenedor.style.display = 'none';
                    return;
                }
                contenedor.style.display = 'block';
                const filtrados = inventarioGlobal.filter(p => p[1].toLowerCase().includes(texto) || p[2].toLowerCase().includes(texto));
                
                if(filtrados.length === 0) {
                    contenedor.innerHTML = '<p>No se encontraron productos.</p>';
                    return;
                }
                contenedor.innerHTML = filtrados.map(p => `
                    <div class="item">
                        <div><b>${p[1]}</b> - ${p[2]}<br><small>Precio: $${p[3]} | Stock: <b>${p[4]}</b></small></div>
                        <button onclick="agregarAlCarrito(${p[0]}, '${p[1]}', '${p[2]}', ${p[3]}, ${p[4]})" style="width:auto; padding:5px 10px;">Agregar</button>
                    </div>
                `).join('');
            }

            function abrirModalInventario() {
                document.getElementById('modal-inventario').style.display = 'block';
                renderizarStockModal();
            }

            function cerrarModalInventario() {
                document.getElementById('modal-inventario').style.display = 'none';
            }

            function renderizarStockModal() {
                const contenedor = document.getElementById('contenido-modal-stock');
                if(inventarioGlobal.length === 0) {
                    contenedor.innerHTML = '<p>No hay productos en el inventario.</p>';
                    return;
                }
                contenedor.innerHTML = inventarioGlobal.map(p => `
                    <div class="item">
                        <div><b>${p[1]}</b> - ${p[2]}<br><small>Precio: $${p[3]} | Stock actual: <b>${p[4]}</b></small></div>
                        <button class="btn-warning" onclick="reponerStock(${p[0]}, '${p[2]}')" style="width:auto; padding:5px 10px;">➕ Reponer</button>
                    </div>
                `).join('');
            }

            function cerrarTodo() {
                document.getElementById('busqueda').value = '';
                document.getElementById('lista-productos').style.display = 'none';
                cerrarModalInventario();
            }

            async function reponerStock(id, nombre) {
                const cantidadExtra = prompt(`¿Cuántas unidades nuevas van a ingresar para "${nombre}"?`);
                if(!cantidadExtra || isNaN(cantidadExtra) || parseInt(cantidadExtra) <= 0) return;

                const res = await fetch('/reponer_stock', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id, cantidad: parseInt(cantidadExtra)})
                });
                const data = await res.json();
                alert(data.mensaje);
                cargarProductos();
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
                let cantidadActual = itemEnCarrito ? itemEnCarrito.cantidad : 0;

                if(cantidadActual < stockMax) {
                    if(itemEnCarrito) {
                        itemEnCarrito.cantidad++;
                    } else {
                        carrito.push({id, codigo, nombre, precio, cantidad: 1});
                    }
                    actualizarCarrito();
                } else {
                    alert('No hay más stock disponible.');
                }
            }

            function actualizarCarrito() {
                const contenedor = document.getElementById('lista-carrito');
                const tasa = parseFloat(document.getElementById('tasa-bcv').value) || 1;

                if(carrito.length === 0) {
                    contenedor.innerHTML = '<p>El carrito está vacío.</p>';
                    document.getElementById('total-dolar').innerText = '0.00';
                    document.getElementById('total-bs').innerText = '0.00';
                    return;
                }

                let totalDolar = 0;
                contenedor.innerHTML = carrito.map(i => {
                    let subtotalDolar = i.precio * i.cantidad;
                    let subtotalBs = subtotalDolar * tasa;
                    totalDolar += subtotalDolar;
                    return `<div class="cart-item">
                        <span><b>${i.nombre}</b> x${i.cantidad}</span>
                        <span>$${subtotalDolar.toFixed(2)} <br><small style="color:gray;">Bs. ${subtotalBs.toFixed(2)}</small></span>
                    </div>`;
                }).join('');

                let totalBs = totalDolar * tasa;
                document.getElementById('total-dolar').innerText = totalDolar.toFixed(2);
                document.getElementById('total-bs').innerText = totalBs.toFixed(2);
            }

            function actualizarCalculos() {
                actualizarCarrito();
            }

            function cancelarCarrito() {
                if(carrito.length === 0) return;
                if(confirm('¿Cancelar la compra actual?')) {
                    carrito = [];
                    actualizarCarrito();
                }
            }

            async function procesarVenta() {
                if(carrito.length === 0) {
                    alert('El carrito está vacío.');
                    return;
                }
                const tasa = parseFloat(document.getElementById('tasa-bcv').value) || 1;
                let totalDolar = carrito.reduce((sum, i) => sum + (i.precio * i.cantidad), 0);
                let totalBs = totalDolar * tasa;

                const res = await fetch('/procesar_venta', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({carrito})
                });
                const data = await res.json();
                
                if(data.success) {
                    alert(`¡Venta procesada con éxito!\nTotal: $${totalDolar.toFixed(2)} (Bs. ${totalBs.toFixed(2)})`);
                    carrito = [];
                    actualizarCarrito();
                    cargarProductos();
                } else {
                    alert('Error al procesar la venta.');
                }
            }

            // Atajos de teclado (F1, F2 o Ctrl+3, Ctrl+4)
            window.addEventListener('keydown', function(e) {
                if (e.key === 'F1') {
                    e.preventDefault();
                    abrirModalInventario();
                } else if (e.key === 'F2') {
                    e.preventDefault();
                    cerrarTodo();
                } else if (e.ctrlKey && e.key === '3') {
                    e.preventDefault();
                    procesarVenta();
                } else if (e.ctrlKey && e.key === '4') {
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

@app.route('/reponer_stock', methods=['POST'])
def reponer_stock():
    data = request.json
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (data['cantidad'], data['id']))
    conn.commit()
    conn.close()
    return jsonify({'mensaje': '¡Stock repuesto con éxito!'})

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
