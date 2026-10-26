from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, precio REAL NOT NULL, stock INTEGER NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, total_usd REAL NOT NULL, total_bs REAL NOT NULL, tasa_bcv REAL NOT NULL, detalles TEXT NOT NULL, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
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
        <title>Sistema POS</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f4f9; margin: 0; padding: 15px; }
            .container { max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            input, button { width: 100%; padding: 10px; margin: 6px 0; box-sizing: border-box; }
            button { background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .btn-success { background: #28a745; }
            .row { display: flex; gap: 20px; flex-wrap: wrap; }
            .col { flex: 1; min-width: 280px; background: #fdfdfd; padding: 15px; border: 1px solid #ddd; border-radius: 6px; }
            .item { background: #fff; padding: 8px; margin-bottom: 5px; border-left: 4px solid #007bff; display: flex; justify-content: space-between; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🛒 Sistema POS Rápido</h2>
            <div class="row">
                <div class="col">
                    <h3>🔍 Buscar Producto</h3>
                    <input type="text" id="busqueda" placeholder="Buscar..." onkeyup="filtrar()">
                    <div id="lista" style="max-height:150px; overflow-y:auto;"></div>
                    
                    <h3 style="margin-top:20px;">➕ Registrar</h3>
                    <input type="text" id="codigo" placeholder="Código">
                    <input type="text" id="nombre" placeholder="Nombre">
                    <input type="number" id="precio" placeholder="Precio ($)" step="0.01">
                    <input type="number" id="stock" placeholder="Stock">
                    <button class="btn-success" onclick="guardar()">Guardar</button>
                </div>
                <div class="col">
                    <h3>🛍️ Carrito</h3>
                    <div id="carrito-lista">Vacío</div>
                    <h3>Total: $<span id="total">0.00</span></h3>
                    <button class="btn-success" onclick="cobrar()">Cobrar</button>
                </div>
            </div>
        </div>
        <script>
            let inv = []; let car = [];
            async function cargar() {
                let res = await fetch('/productos');
                inv = await res.json();
            }
            function filtrar() {
                let q = document.getElementById('busqueda').value.toLowerCase();
                let l = document.getElementById('lista');
                if(!q) { l.innerHTML = ''; return; }
                let res = inv.filter(p => p[1].toLowerCase().includes(q) || p[2].toLowerCase().includes(q));
                l.innerHTML = res.map(p => `<div class="item"><span><b>${p[2]}</b> ($${p[3]})</span><button style="width:auto;padding:4px 8px;" onclick="add(${p[0]},'${p[2]}',${p[3]},${p[4]})">Add</button></div>`).join('');
            }
            async function guardar() {
                let codigo = document.getElementById('codigo').value;
                let nombre = document.getElementById('nombre').value;
                let precio = parseFloat(document.getElementById('precio').value);
                let stock = parseInt(document.getElementById('stock').value);
                let res = await fetch('/agregar', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({codigo,nombre,precio,stock})});
                let d = await res.json(); alert(d.msj); cargar();
            }
            function add(id, nombre, precio, stock) {
                let it = car.find(x => x.id === id);
                if(it) { it.cant++; } else { car.push({id, nombre, precio, cant:1}); }
                renderCar();
            }
            function renderCar() {
                let c = document.getElementById('carrito-lista');
                let tot = 0;
                c.innerHTML = car.map(x => { tot += x.precio * x.cant; return `<div>${x.nombre} x${x.cant} - $${(x.precio*x.cant).toFixed(2)}</div>`; }).join('');
                document.getElementById('total').innerText = tot.toFixed(2);
            }
            async function cobrar() {
                if(car.length === 0) return;
                let res = await fetch('/venta', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({carrito:car})});
                let d = await res.json();
                if(d.ok) { alert('¡Venta exitosa! Total: $' + d.total.toFixed(2)); car = []; renderCar(); cargar(); }
            }
            cargar();
        </script>
    </body>
    </html>
    '''

@app.route('/productos')
def prods():
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute("SELECT id, codigo, nombre, precio, stock FROM productos")
    res = c.fetchall()
    conn.close()
    return jsonify(res)

@app.route('/agregar', methods=['POST'])
def add_p():
    d = request.json
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO productos (codigo, nombre, precio, stock) VALUES (?, ?, ?, ?)", (d['codigo'], d['nombre'], d['precio'], d['stock']))
        conn.commit()
        msj = "Registrado con éxito"
    except:
        msj = "El código ya existe"
    conn.close()
    return jsonify({'msj': msj})

@app.route('/venta', methods=['POST'])
def venta():
    d = request.json
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    tot = 0
    det = ""
    for i in d['carrito']:
        tot += i['precio'] * i['cant']
        det += f"{i['cant']}x {i['nombre']}, "
        c.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (i['cant'], i['id']))
    c.execute("INSERT INTO ventas (total_usd, total_bs, tasa_bcv, detalles) VALUES (?, ?, ?, ?)", (tot, tot*36.5, 36.5, det))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'total': tot})

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
