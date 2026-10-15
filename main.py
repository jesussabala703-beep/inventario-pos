from flask import Flask, render_template_string, request, jsonify
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
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            detalles TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Punto de Venta e Inventario</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container my-4">
        <h2 class="mb-4 text-center">📦 Sistema de Caja e Inventario Rápido</h2>
        <div class="row">
            <div class="col-md-7">
                <div class="card p-3 shadow-sm mb-3">
                    <h4>🔍 Buscar Producto</h4>
                    <div class="input-group mb-3">
                        <input type="text" id="busqueda" class="form-control" placeholder="Escribe el nombre o código..." onkeyup="buscarProductos()">
                    </div>
                    <div style="max-height: 350px; overflow-y: auto;">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Código</th>
                                    <th>Nombre</th>
                                    <th>Precio</th>
                                    <th>Stock</th>
                                    <th>Acción</th>
                                </tr>
                            </thead>
                            <tbody id="resultados-tabla"></tbody>
                        </table>
                    </div>
                </div>
                <div class="card p-3 shadow-sm">
                    <h4>➕ Registrar Producto Nuevo / Llegada</h4>
                    <form id="form-producto" onsubmit="guardarProducto(event)">
                        <div class="row g-2">
                            <div class="col-md-4">
                                <input type="text" id="nuevo-codigo" class="form-control" placeholder="Código" required>
                            </div>
                            <div class="col-md-8">
                                <input type="text" id="nuevo-nombre" class="form-control" placeholder="Nombre" required>
                            </div>
                            <div class="col-md-6">
                                <input type="number" step="0.01" id="nuevo-precio" class="form-control" placeholder="Precio ($)" required>
                            </div>
                            <div class="col-md-6">
                                <input type="number" id="nuevo-stock" class="form-control" placeholder="Cantidad" required>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-success mt-2 w-100">Guardar en Inventario</button>
                    </form>
                </div>
            </div>
            <div class="col-md-5">
                <div class="card p-3 shadow-sm">
                    <h4>🛒 Carrito de Venta</h4>
                    <ul class="list-group mb-3" id="lista-carrito" style="max-height: 250px; overflow-y: auto;">
                        <li class="list-group-item text-muted text-center">El carrito está vacío</li>
                    </ul>
                    <h4>Total: $<span id="total-carrito">0.00</span></h4>
                    <button class="btn btn-primary w-100 mt-2" onclick="procesarVenta()">💳 Cobrar y Generar Factura</button>
                </div>
            </div>
        </div>
    </div>
    <script>
        let carrito = [];
        function buscarProductos() {
            let query = document.getElementById('busqueda').value;
            fetch('/buscar?q=' + query).then(res => res.json()).then(data => {
                let tbody = document.getElementById('resultados-tabla');
                tbody.innerHTML = '';
                data.forEach(p => {
                    tbody.innerHTML += `
                        <tr>
                            <td>${p[1]}</td>
                            <td>${p[2]}</td>
                            <td>$${p[3]}</td>
                            <td><span class="badge bg-${p[4] > 0 ? 'success' : 'danger'}">${p[4]}</span></td>
                            <td><button class="btn btn-sm btn-outline-primary" onclick="agregarAlCarrito(${p[0]}, '${p[1]}', '${p[2]}', ${p[3]}, ${p[4]})">Agregar</button></td>
                        </tr>
                    `;
                });
            });
        }
        function agregarAlCarrito(id, codigo, nombre, precio, stockActual) {
            let cantidadPedida = prompt(`¿Cuántas unidades de "${nombre}" se llevan? (Stock: ${stockActual})`, "1");
            if (!cantidadPedida) return;
            cantidadPedida = parseInt(cantidadPedida);
            if (isNaN(cantidadPedida) || cantidadPedida <=0) { alert("No válida"); return; }
            if (cantidadPedida > stockActual) { alert("¡No hay suficiente stock!"); return; }
            let existente = carrito.find(item => item.id === id);
            if (existente) { existente.cantidad += cantidadPedida; } 
            else { carrito.push({ id, codigo, nombre, precio, cantidad: cantidadPedida }); }
            actualizarCarrito();
        }
        function actualizarCarrito() {
            let lista = document.getElementById('lista-carrito');
            let totalSpan = document.getElementById('total-carrito');
            lista.innerHTML = '';
            let total = 0;
            if (carrito.length === 0) {
                lista.innerHTML = '<li class="list-group-item text-muted text-center">El carrito está vacío</li>';
                totalSpan.innerText = '0.00';
                return;
            }
            carrito.forEach((item, index) => {
                let subtotal = item.precio * item.cantidad;
                total += subtotal;
                lista.innerHTML += `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div><strong>${item.nombre}</strong><br><small>$${item.precio} x ${item.cantidad} = $${subtotal.toFixed(2)}</small></div>
                        <button class="btn btn-sm btn-danger" onclick="eliminarDelCarrito(${index})">X</button>
                    </li>
                `;
            });
            totalSpan.innerText = total.toFixed(2);
        }
        function eliminarDelCarrito(index) { carrito.splice(index, 1); actualizarCarrito(); }
        function guardarProducto(event) {
            event.preventDefault();
            let datos = {
                codigo: document.getElementById('nuevo-codigo').value,
                nombre: document.getElementById('nuevo-nombre').value,
                precio: parseFloat(document.getElementById('nuevo-precio').value),
                stock: parseInt(document.getElementById('nuevo-stock').value)
            };
            fetch('/agregar_producto', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(datos)
            }).then(res => res.json()).then(data => {
                alert(data.mensaje);
                document.getElementById('form-producto').reset();
                buscarProductos();
            });
        }
        function procesarVenta() {
            if (carrito.length === 0) { alert("El carrito está vacío."); return; }
            fetch('/procesar_venta', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ carrito: carrito })
            }).then(res => res.json()).then(data => {
                alert("✅ Venta procesada. Total: $" + data.total.toFixed(2));
                carrito = [];
                actualizarCarrito();
                buscarProductos();
            });
        }
        buscarProductos();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/buscar')
def buscar():
    query = request.args.get('q', '')
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, nombre, precio, stock FROM productos WHERE nombre LIKE ? OR codigo LIKE ?", ('%' + query + '%', '%' + query + '%'))
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
                       (data['codigo'], data['nombre'], data['precio'], data['stock']))
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
        detalles_str += f"{item['cantidad']}x {item['nombre']}, "
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (item['cantidad'], item['id']))
    cursor.execute("INSERT INTO ventas (total, detalles) VALUES (?, ?)", (total_venta, detalles_str))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'total': total_venta})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
