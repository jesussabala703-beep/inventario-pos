from flask import Flask, request, jsonify
import sqlite3
import json
import os

app = Flask(__name__)

JSON_INVENTARIO = 'inventario_inicial.json'

def init_db():
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, precio REAL NOT NULL, stock INTEGER NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, total_usd REAL NOT NULL, total_bs REAL NOT NULL, tasa_bcv REAL NOT NULL, detalles TEXT NOT NULL, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    
    if os.path.exists(JSON_INVENTARIO):
        try:
            with open(JSON_INVENTARIO, 'r', encoding='utf-8') as f:
                items = json.load(f)
                for item in items:
                    try:
                        c.execute("INSERT INTO productos (codigo, nombre, precio, stock) VALUES (?, ?, ?, ?)", 
                                  (item['codigo'], item['nombre'], item['precio'], item['stock']))
                    except sqlite3.IntegrityError:
                        pass
        except Exception as e:
            print("Error leyendo el archivo JSON:", e)

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sistema POS & Inventario</title>
<style>
body { 
    font-family: Arial, sans-serif; 
    background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url('https://i.ibb.co/3yk7v6g/fondo-moto.jpg'); /* Imagen personalizada */
    background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url('https://images.unsplash.com/photo-1558981403-c5f9899a28bc?q=80&w=1920&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    margin: 0; 
    padding: 10px; 
}
.container { 
    max-width: 900px; 
    margin: auto; 
    background: rgba(255, 255, 255, 0.94); 
    backdrop-filter: blur(8px);
    padding: 15px; 
    border-radius: 8px; 
    position: relative; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.4); 
}
input, button { width: 100%; padding: 8px; margin: 5px 0; box-sizing: border-box; border-radius: 4px; border: 1px solid #ccc; font-size: 14px; }
button { background: #34495e; color: white; border: none; cursor: pointer; font-weight: bold; }
button:hover { background: #2c3e50; }
.btn-success { background: #27ae60 !important; }
.btn-success:hover { background: #219653 !important; }
.btn-danger { background: #7f8c8d; color: white; } /* Cambiado a gris sobrio */
.btn-warning { background: #7f8c8d; color: white; } /* Cambiado a gris sobrio */
.row { display: flex; flex-wrap: wrap; gap: 15px; }
.col { flex: 1; min-width: 270px; background: rgba(250, 250, 250, 0.95); padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
.item-list, .cart-list { max-height: 180px; overflow-y: auto; border: 1px solid #ddd; padding: 5px; background: #fff; }
.item { background: #fff; padding: 6px; margin-bottom: 4px; border-left: 4px solid #34495e; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
.stock-low { border-left-color: #c0392b !important; background: #fdf2e9; }
.cart-item { background: #fff; padding: 5px; margin-bottom: 3px; border-left: 4px solid #7f8c8d; font-size: 13px; display: flex; justify-content: space-between; }
.bcv-box { position: absolute; top: 15px; right: 15px; background: rgba(232, 248, 245, 0.95); border: 1px solid #a3e4d7; padding: 5px 10px; border-radius: 6px; text-align: right; font-size: 12px; color: #16a085; }
.bcv-box input { width: 75px; padding: 2px; text-align: center; font-weight: bold; margin-left: 5px; }
.modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); }
.modal-content { background: white; margin: 5% auto; padding: 15px; width: 90%; max-width: 600px; border-radius: 8px; max-height: 80vh; overflow-y: auto; }
.close-modal { float: right; background: #7f8c8d; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; width: auto; }
.ticket-box { font-family: monospace; background: #fff8dc; padding: 10px; border: 1px dashed #333; margin-top: 10px; font-size: 13px; }
.badge-low { background: #c0392b; color: white; font-size: 9px; padding: 2px 4px; border-radius: 3px; }
</style>
</head>
<body>
<div class="container">
<div class="bcv-box">Tasa BCV: <input type="number" id="tasa" value="36.50" step="0.01" onchange="calc()"> Bs/$</div>
<h2>🛒 Sistema POS & Inventario</h2>
<div class="row">
<div class="col">
<h3>🔍 Búsqueda Principal</h3>
<input type="text" id="busq" placeholder="Buscar producto..." onkeyup="filtrar()">
<div style="display:flex; gap:5px;">
<button class="btn-warning" onclick="verStock()">📦 Stock Completo [F1]</button>
<button class="btn-warning" onclick="limpiar()">❌ Limpiar [F2]</button>
</div>
<div id="lista" class="item-list" style="display:none;"></div>
<h3 style="margin-top:15px;">➕ Registrar Nuevo</h3>
<input type="text" id="reg-cod" placeholder="Código">
<input type="text" id="reg-nom" placeholder="Nombre">
<input type="number" id="reg-pre" placeholder="Precio ($)" step="0.01">
<input type="number" id="reg-can" placeholder="Stock inicial">
<button style="background:#34495e;" onclick="guardar()">Guardar</button>
</div>
<div class="col">
<h3>🛍️ Carrito</h3>
<div id="carrito" class="cart-list"><p>Vacío</p></div>
<h3 style="margin-top:10px;">Total: $<span id="tot-d">0.00</span><br><small style="color:#27ae60;">Bs. <span id="tot-b">0.00</span></small></h3>
<button class="btn-success" onclick="cobrar()">🖨️ Cobrar / Confirmar Venta [Ctrl+3]</button>
<button class="btn-danger" onclick="cancelar()" style="margin-top:4px;">❌ Cancelar [Ctrl+4]</button>
<button style="margin-top:10px; background:#34495e;" onclick="verVentas()">📊 Reporte de Ventas</button>
</div>
</div>
</div>

<div id="modal-stk" class="modal">
    <div class="modal-content">
        <button class="close-modal" onclick="cerrarModal('modal-stk')">Cerrar</button>
        <h3>📦 Inventario, Reposición y Ajuste Admin</h3>
        <input type="text" id="busq-modal" placeholder="🔍 Buscar en el stock completo..." onkeyup="renderStk()" style="margin-bottom:10px;">
        <div id="cont-stk"></div>
    </div>
</div>

<div id="modal-ven" class="modal"><div class="modal-content"><button class="close-modal" onclick="cerrarModal('modal-ven')">Cerrar</button><h3>📊 Reporte de Ventas</h3><div id="cont-ven"></div></div></div>
<div id="modal-tic" class="modal"><div class="modal-content"><button class="close-modal" onclick="cerrarModal('modal-tic')">Cerrar</button><h3>🧾 Ticket Digital</h3><div id="cont-tic" class="ticket-box"></div><button class="btn-success" onclick="cerrarModal('modal-tic')" style="margin-top:10px;">Aceptar</button></div></div>

<script>
let inv = [], cart = [];

// Función para formatear números estilo venezolano: 10.000,00
function formatoMoneda(num) {
    return num.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function cargar() {
    let r = await fetch('/productos');
    inv = await r.json();
    if(document.getElementById('modal-stk').style.display === 'block') renderStk();
}
function filtrar() {
    let q = document.getElementById('busq').value.toLowerCase().trim();
    let l = document.getElementById('lista');
    let tasa = parseFloat(document.getElementById('tasa').value) || 1;
    if(!q) { l.style.display = 'none'; return; }
    l.style.display = 'block';
    let res = inv.filter(p => p[1].toLowerCase().includes(q) || p[2].toLowerCase().includes(q));
    l.innerHTML = res.length === 0 ? '<p>Sin resultados</p>' : res.map(p => `
        <div class="item ${p[4]<=3?'stock-low':''}">
            <div><b>${p[1]}</b> - ${p[2]} ${p[4]<=3?'<span class="badge-low">BAJO</span>':''}<br><small>$${formatoMoneda(p[3])} (Bs. ${formatoMoneda(p[3]*tasa)}) | Stock: ${p[4]}</small></div>
            <button onclick="add(${p[0]},'${p[2]}',${p[3]},${p[4]})" style="width:auto;padding:4px 8px;">Add</button>
        </div>`).join('');
}
function verStock() { 
    document.getElementById('modal-stk').style.display = 'block'; 
    document.getElementById('busq-modal').value = '';
    renderStk(); 
}
function renderStk() {
    let q = document.getElementById('busq-modal') ? document.getElementById('busq-modal').value.toLowerCase().trim() : '';
    let tasa = parseFloat(document.getElementById('tasa').value) || 1;
    let filtrados = inv.filter(p => p[1].toLowerCase().includes(q) || p[2].toLowerCase().includes(q));
    
    document.getElementById('cont-stk').innerHTML = filtrados.length === 0 ? '<p>No se encontraron productos</p>' : filtrados.map(p => `
        <div class="item ${p[4]<=3?'stock-low':''}">
            <div>
                <b>${p[1]}</b> - ${p[2]} ${p[4]<=3?'<span class="badge-low">BAJO</span>':''}<br>
                <small>Precio: <b>$${formatoMoneda(p[3])}</b> (<b>Bs. ${formatoMoneda(p[3]*tasa)}</b>) | Stock: <b>${p[4]}</b></small>
            </div>
            <div style="display:flex; gap:4px;">
                <button class="btn-warning" onclick="reponer(${p[0]},'${p[2]}')" style="width:auto;padding:4px 8px;" title="Sumar stock">➕</button>
                <button class="btn-danger" onclick="ajustarAdmin(${p[0]},'${p[2]}',${p[4]})" style="width:auto;padding:4px 8px;" title="Ajuste Admin">⚙️ Admin</button>
            </div>
        </div>`).join('');
}
async function reponer(id, nom) {
    let cant = prompt(`Unidades a sumar para "${nom}":`);
    if(!cant || isNaN(cant) || cant<=0) return;
    await fetch('/reponer', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id, cantidad:parseInt(cant)})});
    cargar();
}
async function ajustarAdmin(id, nom, stockActual) {
    let pass = prompt("🔑 Ingrese contraseña de Administrador:");
    if(pass !== "admin123") {
        if(pass !== null) alert("Contraseña incorrecta.");
        return;
    }
    let nuevoStock = prompt(`[MODO ADMIN] Ajuste manual para "${nom}". Stock actual: ${stockActual}\\nIngrese el stock real correcto:`);
    if(nuevoStock === null || isNaN(nuevoStock)) return;
    
    let res = await fetch('/ajuste_admin', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id, stock: parseInt(nuevoStock)})
    });
    let d = await res.json();
    alert(d.msj);
    cargar();
}
function cerrarModal(id) { document.getElementById(id).style.display = 'none'; }
function limpiar() { document.getElementById('busq').value = ''; document.getElementById('lista').style.display = 'none'; }
async function guardar() {
    let codigo = document.getElementById('reg-cod').value;
    let nombre = document.getElementById('reg-nom').value;
    let precio = parseFloat(document.getElementById('reg-pre').value);
    let stock = parseInt(document.getElementById('reg-can').value);
    if(!codigo || !nombre || isNaN(precio) || isNaN(stock)) { alert('Completa todos los campos'); return; }
    let r = await fetch('/agregar', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({codigo,nombre,precio,stock})});
    let d = await r.json(); alert(d.msj);
    document.getElementById('reg-cod').value = ''; document.getElementById('reg-nom').value = ''; document.getElementById('reg-pre').value = ''; document.getElementById('reg-can').value = '';
    cargar();
}
function add(id, nombre, precio, stock) {
    let item = cart.find(x => x.id === id);
    let cant = item ? item.cant : 0;
    if(cant < stock) {
        if(item) item.cant++; else cart.push({id, nombre, precio, cant:1});
        renderCart();
    } else { alert('Stock máximo alcanzado'); }
}
function renderCart() {
    let c = document.getElementById('carrito');
    let tasa = parseFloat(document.getElementById('tasa').value) || 1;
    if(cart.length === 0) { c.innerHTML = '<p>Vacío</p>'; document.getElementById('tot-d').innerText = '0,00'; document.getElementById('tot-b').innerText = '0,00'; return; }
    let totD = 0;
    c.innerHTML = cart.map(x => {
        let sub = x.precio * x.cant;
        totD += sub;
        return `<div class="cart-item"><span><b>${x.nombre}</b> x${x.cant}</span><span>$${formatoMoneda(sub)}<br><small>Bs. ${formatoMoneda(sub*tasa)}</small></span></div>`;
    }).join('');
    document.getElementById('tot-d').innerText = formatoMoneda(totD);
    document.getElementById('tot-b').innerText = formatoMoneda(totD * tasa);
}
function calc() { 
    renderCart(); 
    if(document.getElementById('modal-stk').style.display === 'block') renderStk();
    let q = document.getElementById('busq').value;
    if(q) filtrar();
}
function cancelar() { if(cart.length && confirm('¿Cancelar compra?')) { cart = []; renderCart(); } }
async function cobrar() {
    if(cart.length === 0) { alert('Carrito vacío'); return; }
    let tasa = parseFloat(document.getElementById('tasa').value) || 1;
    let totD = cart.reduce((s, x) => s + (x.precio * x.cant), 0);
    let r = await fetch('/venta', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({carrito:cart, tasa})});
    let d = await r.json();
    if(d.ok) {
        let tic = `<center><b>COMPROBANTE DE VENTA</b><br><small>${new Date().toLocaleString()}</small></center><hr>` +
                  cart.map(x => `<div>${x.cant}x ${x.nombre} <span style="float:right;">$${formatoMoneda(x.precio*x.cant)}</span></div>`).join('') +
                  `<hr><b>Tasa:</b> Bs. ${formatoMoneda(tasa)}<br><b>Total ($):</b> $${formatoMoneda(totD)}<br><b>Total (Bs):</b> Bs. ${formatoMoneda(totD*tasa)}<hr><center><small>¡Gracias!</small></center>`;
        document.getElementById('cont-tic').innerHTML = tic;
        document.getElementById('modal-tic').style.display = 'block';
        cart = []; renderCart(); cargar();
    }
}
async function verVentas() {
    document.getElementById('modal-ven').style.display = 'block';
    let r = await fetch('/ventas');
    let v = await r.json();
    let c = document.getElementById('cont-ven');
    if(v.length === 0) { c.innerHTML = '<p>No hay ventas</p>'; return; }
    let totUSD = 0, totBS = 0;
    let html = v.map(x => {
        totUSD += x[1]; totBS += x[2];
        return `<div style="background:#f4f6f7;padding:8px;margin-bottom:6px;border-left:4px solid #34495e;font-size:13px;"><b>Fecha:</b> ${x[5]}<br><b>Detalle:</b> ${x[4]}<br><b>Total:</b> $${formatoMoneda(x[1])} (Bs. ${formatoMoneda(x[2])})</div>`;
    }).join('');
    c.innerHTML = `<div style="background:#e8daef;padding:8px;margin-bottom:10px;border-radius:4px;"><b>Total USD:</b> $${formatoMoneda(totUSD)}<br><b>Total VES:</b> Bs. ${formatoMoneda(totBS)}</div>` + html;
}
window.addEventListener('keydown', e => {
    if(e.key==='F1'){ e.preventDefault(); verStock(); }
    else if(e.key==='F2'){ e.preventDefault(); limpiar(); cerrarModal('modal-stk'); cerrarModal('modal-ven'); cerrarModal('modal-tic'); }
    else if(e.ctrlKey && e.key==='3'){ e.preventDefault(); cobrar(); }
    else if(e.ctrlKey && e.key==='4'){ e.preventDefault(); cancelar(); }
});
cargar();
</script>
</body>
</html>'''

@app.route('/productos')
def prods():
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute("SELECT id, codigo, nombre, precio, stock FROM productos")
    r = c.fetchall(); conn.close()
    return jsonify(r)

@app.route('/agregar', methods=['POST'])
def add_p():
    d = request.json
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO productos (codigo, nombre, precio, stock) VALUES (?, ?, ?, ?)", (d['codigo'], d['nombre'], d['precio'], d['stock']))
        conn.commit(); msj = "Guardado con éxito"
    except: msj = "El código ya existe"
    conn.close()
    return jsonify({'msj': msj})

@app.route('/reponer', methods=['POST'])
def rep():
    d = request.json
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (d['cantidad'], d['id']))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

@app.route('/ajuste_admin', methods=['POST'])
def ajuste_admin():
    d = request.json
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute("UPDATE productos SET stock = ? WHERE id = ?", (d['stock'], d['id']))
    conn.commit(); conn.close()
    return jsonify({'msj': '¡Stock ajustado correctamente por Administrador!'})

@app.route('/venta', methods=['POST'])
def venta():
    d = request.json
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    tot = 0; det = ""
    for i in d['carrito']:
        tot += i['precio'] * i['cant']
        det += f"{i['cant']}x {i['nombre']} (${i['precio']}), "
        c.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (i['cant'], i['id']))
    tot_bs = tot * d['tasa']
    c.execute("INSERT INTO ventas (total_usd, total_bs, tasa_bcv, detalles) VALUES (?, ?, ?, ?)", (tot, tot_bs, d['tasa'], det))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

@app.route('/ventas')
def get_v():
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute("SELECT id, total_usd, total_bs, tasa_bcv, detalles, fecha FROM ventas ORDER BY id DESC")
    r = c.fetchall(); conn.close()
    return jsonify(r)

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)