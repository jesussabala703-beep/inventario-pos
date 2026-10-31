def init_db():
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, precio REAL NOT NULL, stock INTEGER NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, total_usd REAL NOT NULL, total_bs REAL NOT NULL, tasa_bcv REAL NOT NULL, detalles TEXT NOT NULL, fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

    # Sincronización automática con el JSON en la nube
    if os.path.exists(JSON_INVENTARIO):
        try:
            with open(JSON_INVENTARIO, 'r', encoding='utf-8') as f:
                items = json.load(f)
                for item in items:
                    c.execute("""
                        INSERT INTO productos (codigo, nombre, precio, stock) 
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(codigo) DO UPDATE SET 
                        nombre=excluded.nombre, 
                        precio=excluded.precio
                    """, (item['codigo'], item['nombre'], item['precio'], item['stock']))
        except Exception as e:
            print("Error leyendo o sincronizando el archivo JSON:", e)

    conn.commit()
    conn.close()