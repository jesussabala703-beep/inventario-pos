import sqlite3

# Datos extraídos directamente de la lista PVP (Nombre, PVP Cobro)
repuestos = [
    ("PARRILLA SBR MF", 14.00),
    ("ACEITE SHELL MINERAL 20W-50 (LITRO)", 18.00),
    ("AMORTIGUADOR GY6 SCOOTER MF", 23.00),
    ("AMORTIGUADOR TRASERO BRF MP", 24.00),
    ("AMORTIGUADOR TRASERO EXPRESS MP", 24.00),
    ("ARANDELA EMPACADURA TUBO ESCAPE CG150", 0.20),
    ("ARANDELA EMPACADURA TUBO ESCAPE GY6", 0.20),
    ("ARRANQUE COMPLETO CG150 MP", 19.00),
    ("ARRANQUE COMPLETO GRIS CG200 MP", 19.00),
    ("ASIENTO GN 125 MF", 23.00),
    ("ASIENTO HORSE MF", 18.00),
    ("BASTON EXPRESS DE RAYO PAR MP", 43.00),
    ("BASTON HORSE MF", 52.00),
    ("BASTON SBR PAR MP", 54.00),
    ("BATERIA DE SCOOTER YTX7A MP", 23.00),
    ("BATERIA SECA 12N6.5 MP", 20.00),
    ("BOMBA DE AIRE DE BICICLETA GRANDE MP", 3.50),
    ("BOMBILLO CRUCE UNIV MP", 0.25),
    ("BOMBILLO LED BLANCO DOS CONTACTOS MP", 4.00),
    ("BOMBILLO LED H4 BLANCO MP", 4.00),
    ("BOMBILLO STOP 12V MF (UNIDAD)", 2.60),
    ("BOMBILLO ZOOM PRO MAX CROW LED 50.000LM", 17.00),
    ("BUJE PORTA CORONA CG150 MP", 1.00),
    ("CALIPER DELANTERO CG150 MP", 12.00),
    ("CALIPER DELANTERO CGB MP", 12.00),
    ("CALIPER DELANTERO HORSE MP", 12.00),
    ("CASCO JAGUAR SOLID SEMI-INTEGRAL NEGRO S", 49.00),
    ("CASCO JAGUAR SOLID SEMI-INTEGRAL NEGRO M", 49.00),
    ("CASCO JAGUAR SOLID GRIS MATE L", 46.00),
    ("CASCO SANDOVAL OVAL", 7.00),
    ("CAUCHO 2.50/18 MP533 MOTOR POWER", 16.00),
    ("CAUCHO 2.75/18 MP219 MOTOR POWER", 18.50),
    ("CAUCHO 90/90/18 MP 592", 26.00),
    ("CDI HORSE PROGRESIVO MP", 37.00),
    ("CONECTOR CDI CG150 MP", 0.50),
    ("CONTRAPESO VOLANTE HORSE CROMADO MF", 2.70),
    ("CONTRAPESO CROMADO CG150 MP", 3.80),
    ("CORONA GN/HORSE/CG150 37T DORAO PUNTA NEGRA", 4.00),
    ("CORONA GN/HORSE/CG150 38T DORAO PUNTA NEGRA", 3.80),
    ("CORONA GN/HORSE/CG150 39T DORAO PUNTA NEGRA", 4.00),
    ("CORONA MD/EXPREES 39T OVALADA DORAD PN MP", 3.60),
    ("CORREA GY6 835-20-30 MP", 4.00),
    ("CROCHERA COMPLETA SCOOTER MF", 28.50),
    ("CUCHARITA CG150 MP", 3.70),
    ("CUENTA KILOMETRAJE HORSE MP", 5.00),
    ("CUENTA KILOMETRAJE SBR MP", 3.00),
    ("DISCO DE CROCHE 6 PIEZAS CG150 LUBRICADO", 2.75),
    ("DISCO DE CROCHE 6 PIEZAS CG150 MP", 5.20),
    ("LATA MP", 3.25),
    ("EJE DELANTERO HORSE MP", 1.10),
    ("EJE PEDAL CAMBIO CG150 CON CACHOS MP", 2.40),
    ("EJE PEDAL DE ARRANQUE CG150 MP", 1.50),
    ("EJE TRASERO SBR MP", 0.50),
    ("EMBLEMA BERA", 2.50),
    ("EMPACADURA TAPA CROCHERA CG150 MP", 0.40),
    ("EMPACADURA MAGNETO CG150 MF", 0.80),
    ("ENGANCHE ARRANQUE CG150 MP", 7.00),
    ("FLASHER UNIVERSAL MP", 1.30),
    ("GUARDAFANGO DELANTERO CGB AZUL MP", 8.50),
    ("GUARDAFANGO DELANTERO CGB ROJO MP", 5.80),
    ("GUARDAFANGO DELANTERO OWEN NEGRO MP", 1.50),
    ("GUAYA DE KILOMETRAJE C/FORRO CGB MP", 0.70),
    ("HORQUILLA/TUERA CGB NEGRO MP", 5.60),
    ("INSTALACION/RAMAL SBR MF", 6.00),
    ("KIT DE REPARACION CALIPER CGB MP", 5.20),
    ("KIT DE RESORTE CG150 MP", 10.00),
    ("KIT GOMA PARA TANQUE SBR MF", 6.00),
    ("KIT PISTON STD CG200 MP", 15.00),
    ("KIT PISTON STD CG150 MP", 1.50),
    ("KIT PISTON STD CGB MP", 0.80),
    ("KIT PISTON STD GY6 MP", 0.70),
    ("KIT PISTON STD HORSE ALTA CALIDAD CAJA LATA MP", 0.60),
    ("KIT PISTON STD HORSE MP", 1.00),
    ("KIT RELACION MD 38T/1ST CADENA DORADO 120L", 2.00),
    ("KIT REPARACION CLUTCHERA CG150 MP", 1.90),
    ("KIT TORNILLO PORTA CORONA CG150 MP", 2.20),
    ("LEVA BANDA CG150 MP", 7.70),
    ("LLAVE GASOLINA CG150 MP", 3.00),
    ("LUZ CRUCE HORSE MP", 1.20),
    ("LUZ CRUCE SBR MF", 6.00),
    ("MANDO SBR MF", 2.30),
    ("MANGUERA DE FRENO SBR MF", 2.50),
    ("MINI KIT DE EMPACADURAS CG150 MP", 2.30),
    ("OREJERA/BASE FARO SBR MP", 3.10),
    ("PATA PARAR C/RESORTE CG150 MP", 3.90),
    ("PATA PARAR C/RESORTE GN125 MP", 1.30),
    ("PATA PARAR C/RESORTE HORSE MP", 1.20),
    ("PECHERA PVC MORADO", 15.00),
    ("PIÑON 15T HORSE/CG150 MP", 12.50),
    ("TACOMETRO BRF HONGJU", 32.00)
]

def cargar_datos():
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()
    
    # Crear la tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    
    agregados = 0
    for idx, (nombre, precio) in enumerate(repuestos, start=1):
        codigo = f"REP-{idx:03d}" # Genera códigos automáticos como REP-001, REP-002, etc.
        stock_inicial = 10        # Asigna un stock base inicial por defecto
        
        try:
            cursor.execute("INSERT INTO productos (codigo, nombre, precio, stock) VALUES (?, ?, ?, ?)",
                           (codigo, nombre, precio, stock_inicial))
            agregados += 1
        except sqlite3.IntegrityError:
            pass # Si el código ya existía, lo omite para no duplicar

    conn.commit()
    conn.close()
    print(f"¡Proceso finalizado! Se registraron {agregados} repuestos correctamente en la base de datos.")

if __name__ == '__main__':
    cargar_datos()
