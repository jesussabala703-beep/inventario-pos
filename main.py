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
            total_usd REAL NOT NULL,
            total_bs REAL NOT NULL,
            tasa_bcv REAL NOT NULL,
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
        <title>Sistema POS & Inventario Avanzado</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 15px; }
            .container { max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); position: relative; }
            h2, h3 { color: #1a252f; margin-top: 0; }
            input, button { width: 100%; padding: 10px; margin: 6px 0; box-sizing: border-box; border-radius: 4px; border: 1px solid #ccc; }
            button { background: #2980b9; color: white; border: none; cursor: pointer; font-size: 14px; font-weight: bold; }
            button:hover { background: #3498db; }
            .btn-success { background: #27ae60; }
            .btn-success:hover { background: #2ecc71; }
            .btn-danger { background: #c0392b; }
            .btn-danger:hover { background: #e74c3c; }
            .btn-warning { background: #f39c12; color: white; }
            .btn-warning:hover { background: #f1c40f; }
            .row { display: flex; flex-wrap: wrap; gap: 20px; }
            .col { flex: 1; min-width: 290px; background: #fafafa; padding: 15px; border: 1px solid #e1e8ed; border-radius: 6px; }
            .item-list, .cart-list { margin-top: 10px; max-height: 220px; overflow-y: auto; border: 1px solid #e1e8ed; padding: 8px; background: #fff; }
            .item { background: #fff; padding: 8px; margin-bottom: 6px; border-left: 4px solid #2980b9; display: flex; justify-content: space-between; align-items: center; border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            .stock-low { border-left-color: #e74c3c !important; background: #fdf2e9; }
            .cart-item { background: #fff; padding: 6px; margin-bottom: 4px; border-left: 4px solid #27ae60; font-size: 14px; display: flex; justify-content: space-between; }
            
            .bcv-box { position: absolute; top: 20px; right: 20px; background: #e8f8f5; border: 1px solid #a3e4d7; padding: 8px 12px; border-radius: 6px; text-align: right; font-size: 13px; color: #16a085; }
            .bcv-box input { width: 85px; padding: 4px; text-align: center; font-weight: bold; margin-left: 5px; }

            .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); }
            .modal-content { background: white; margin: 5% auto; padding: 20px; width: 90%; max-width: 650px; border-radius: 8px; max-height: 80vh; overflow-y: auto; }
            .close-modal { float: right; background: #c0392b; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; width: auto; }
            
            .ticket-box { font-family: 'Courier New', Courier, monospace; background: #fff8dc; padding: 15px; border: 1px dashed #333; margin-top: 10px; }
            .badge-low { background: #e74c3c; color: white; font-size: 10px; padding: 2px 5px; border-radius: 3px; margin-left: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="bcv-box">
                <b>Tasa BCV:</b> <input type="number" id="tasa-bcv" value="36.50" step="0.01" onchange="actualizarCalculos()"> Bs/$
            </div>

            <h2>🛒 Sistema POS & Control de Inventario</h2>
            
            <div class="row">
                <div class="col">
                    <h3>🔍 Búsqueda de Productos</h3>
                    <input type="text" id="busqueda" placeholder="Buscar por código o nombre (ej. repuesto)..." onkeyup="filtrarProductos()" autofocus>
                    
                    <div style="display: flex; gap: 5px; margin-top: 5px;">
                        <button class="btn-warning" onclick="abrirModalInventario()">📦 Stock Completo [F1]</button>
                        <button class="btn-warning" onclick="cerrarTodo()">❌ Limpiar [F2]</button>
                    </div>

                    <div class="item-list" id="lista-productos" style="display:none;"></div>

                    <h3 style="margin-top:20px;">➕ Registrar Producto Nuevo</h3>
                    <input type="text" id="reg-codigo" placeholder="Código de barras / Identificador">
                    <input type="text" id="reg-nombre" placeholder="Descripción del producto">
                    <input type="number" id="reg-precio" placeholder="Precio ($)" step="0.01">
                    <input type="number" id="reg-cantidad" placeholder="Cantidad / Stock Inicial">
                    <button class="btn-success" onclick="guardarProducto()">Guardar en Registro</button>
                </div>

                <div class="col">
                    <h3>🛍️ Carrito de Venta</h3>
                    <div class="cart-list" id="lista-carrito" style="display: block;">
                        <p>El carrito está vacío.</p>
                    </div>
                    <h3 style="margin-top:15px;">
                        Total: $<span id="total-dolar">0.00</span><br>
                        <small style="color: #27ae60;">Bs. <span id="total-bs">0.00</span></small>
                    </h3>
                    
                    <button class="btn-success" onclick="procesarVenta()">🖨️ Cobrar / Generar Factura [Ctrl+3]</button>
                    <button class="btn-danger" onclick="cancelarCarrito()" style="margin-top: 5px;">❌ Cancelar Compra [Ctrl+4]</button>
                    <button style="margin-top: 15px; background: #8e44ad;" onclick="abrirModalVentas()">📊 Ver Reporte de Ventas del Día</button>
                </div>
            </div>
        </div>

        <div id="modal-inventario" class="modal">
            <div class="modal-content">
                <button class="close-modal" onclick="cerrarModalInventario()">Cerrar [F2]</button>
                <h3>📦 Gestión de Inventario y Reposición</h3>
                <div id="contenido-modal-stock">Cargando...</div>
            </div>
        </div>

        <div id="modal-ventas" class="modal">
            <div class="modal-content">
                <button class="close-modal" onclick="cerrarModalVentas()">Cerrar</button>
                <h3>📊 Historial de Ventas y Corte de Caja</h3>
                <div id="contenido-modal-ventas">Cargando ventas...</div>
            </div>
        </div>

        <div id="modal-ticket" class="modal">
            <div class="modal-content">
                <button class="close-modal" onclick="cerrarModalTicket()">Cerrar Comprobante</button>
                <h3>🧾 Comprobante Digital de Venta</h3>
                <div id="contenido-ticket" class="ticket-box"></div>
                <button class="btn-success" onclick="cerrarModalTicket()" style="margin-top: 10px;">Confirmar y Finalizar</button>
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
                    contenedor.innerHTML = '<p>No se encontraron coincidencias.</p>';
                    return;
                }
                contenedor.innerHTML = filtrados.map(p => {
                    const esBajo = p[4] <= 3;
                    return `
                    <div class="item ${esBajo ? 'stock-low' : ''}">
                        <div>
                            <b>${p[1]}</b> - ${p[2]} ${esBajo ? '<span class="badge-low">¡STOCK BAJO!</span>' : ''}<br>
                            <small>Precio: $${p[3]} | Stock: <b>${p[4]}</b></small>
                        </div>
                        <button onclick="agregarAlCarrito(${p[0]}, '${p[1]}', '${p[2]}', ${p[3]}, ${p[4]})" style="width:auto; padding:5px 10px;">Agregar</button>
                    </div>`;
                }).join('');
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
                    contenedor.innerHTML = '<p>No existen registros en la base de datos.</p>';
                    return;
                }
                contenedor.innerHTML = inventarioGlobal.map(p => {
                    const esBajo = p[4] <= 3;
                    return `
                    <div class="item ${esBajo ? 'stock-low' : ''}">
                        <div>
                            <b>${p[1]}</b> - ${p[2]} ${esBajo ? '<span class="badge-low">¡STOCK BAJO!</span>' : ''}<br>
                            <small>Precio: $${p[3]} | Stock actual: <b>${p[4]}</b></small>
                        </div>
                        <button class="btn-warning" onclick="reponerStock(${p[0]}, '${p[2]}')" style="width:auto; padding:5px 10px;">➕ Reponer</button>
                    </div>`;
                }).join('');
            }

            async function abrirModalVentas() {
                document.getElementById('modal-ventas').style.display = 'block';
                const res = await fetch('/obtener_ventas');
                const ventas = await res.json();
                const contenedor = document.getElementById('contenido-modal-ventas');
                
                if(ventas.length === 0) {
                    contenedor.innerHTML = '<p>No se registran ventas en la jornada actual.</p>';
                    return;
                }

                let acumuladoUSD = 0;
                let acumuladoBS = 0;

                let html = '<div style="margin-bottom:15px;">';
                html += ventas.map(v => {
                    acumuladoUSD += v[1];
                    acumuladoBS += v[2];
                    return `
                    <div style="background:#f4f6f7; padding:10px; margin-bottom:8px; border-left:4px solid #8e44ad; border-radius:4px;">
                        <small><b>Fecha/Hora:</b> ${v[5]} | <b>Tasa BCV:</b> ${v[3]} Bs/$</small><br>
                        <b>Detalle:</b> ${v[4]}<br>
                        <b>Total Venta:</b> $${v[1].toFixed(2)} (Bs. ${v[2].toFixed(2)})
                    </div>`;
                }).join('');
                html += '</div>';
                
                html = `
                <div style="background:#e8daef; padding:12px; border-radius:6px; margin-bottom:15px; color:#5b2c6f;">
                    <h4 style="margin:0;">Resumen del Corte de Caja:</h4>
                    <b>Total Recaudado (USD):</b> $${acumuladoUSD.toFixed(2)}<br>
                    <b>Total Recaudado (VES):</b> Bs. ${acumuladoBS.toFixed(2)}
                </div>` + html;

                contenedor.innerHTML = html;
            }

            function cerrarModalVentas() {
                document.getElementById('modal-ventas').style.display = 'none';
            }

            function cerrarModalTicket() {
                document.getElementById('modal-ticket').style.display = 'none';
            }

            function cerrarTodo() {
                document.getElementById('busqueda').value = '';
                document.getElementById('lista-productos').style.display = 'none';
                cerrarModalInventario();
            }

            async function reponerStock(id, nombre) {
                const cantidadExtra = prompt(`Unidades a ingresar para "${nombre}":`);
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
                    alert('Límite de stock alcanzado para este ítem.');
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
                if(confirm('¿Desea vaciar los ítems del carrito actual?')) {
                    carrito = [];
                    actualizarCarrito();
                }
            }

            async function procesarVenta() {
                if(carrito.length === 0) {
                    alert('El carrito no contiene productos.');
                    return;
                }
                const tasa = parseFloat(document.getElementById('tasa-bcv').value) || 1;
                let totalDolar = carrito.reduce((sum, i) => sum + (i.precio * i.cantidad), 0);
                let totalBs = totalDolar * tasa;

                const res = await fetch('/procesar_venta', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({carrito, tasa})
                });
                const data = await res.json();
                
                if(data.success) {
                    let fechaActual = new Date().toLocaleString();
                    let ticketHTML = `
                        <center>
                            <b>SISTEMA DE CONTROL & PUNTO DE VENTA</b><br>
                            <small>Comprobante de Pago Digital</small><br>
                            <small>Fecha: ${fechaActual}</small>
                        </center>
                        <hr style="border-top: 1px dashed #333;">
                        ${carrito.map(i => `
                            <div>${i.cantidad}x ${i.nombre}<span style="float:right;">$${(i.precio * i.cantidad).toFixed(2)}</span></div>
                        `).join('')}
                        <hr style="border-top: 1px dashed #333;">
                        <div><b>Tasa de Cambio:</b> <span style="float:right;">Bs. ${tasa.toFixed(2)}</span></div>
                        <div><b>Total a Pagar ($):</b> <span style="float:right;">$${totalDolar.toFixed(2)}</span></div>
                        <div><b>Total a Pagar (Bs):</b> <span style="float:right;">Bs. ${totalBs.toFixed(2)}</span></div>
                        <hr style="border-top: 1px dashed #333;">
                        <center><small>¡Gracias por su compra!</small></center>
                    `;
                    document.getElementById('contenido-ticket').innerHTML = ticketHTML;
                    document.getElementById('modal-ticket').style.display = 'block';

                    carrito = [];
                    actualizarCarrito();
                    cargarProductos();
         