from flask import Flask, jsonify, request
import pyodbc
from decimal import Decimal
import os

app = Flask(__name__)

# Configura la conexión a la base de datos SQL Server
def connect_to_db():
    SQL_driver = '{ODBC Driver 17 for SQL Server}'
    SQL_server = r'192.168.50.169\Datahouse,1433'
    SQL_database = 'Piamonte_Quiter'
    SQL_username = 'piaQuiter'
    SQL_password = 'piaQuiter'

    conn = pyodbc.connect(f'DRIVER={SQL_driver};'
                          f'SERVER={SQL_server};'
                          f'DATABASE={SQL_database};'
                          f'UID={SQL_username};'
                          f'PWD={SQL_password}')
    return conn

# Constantes para cálculos
IVA_RATE = Decimal('0.19')  # 19%
DISCOUNT_RATE = Decimal('0.20')  # 20%

# Función para formatear el precio con reglas específicas
def format_precio(precio):
    base = int(precio // 1000) * 1000  # Redondeo a la base de mil más cercana
    ajuste = 990 if precio % 1000 >= 500 else 490  # Aplicar la regla de redondeo
    return base + ajuste

# Función para calcular el precio con IVA y descuento
def calcular_precio_con_descuento(precio):
    if precio is None:
        return 0  # O algún valor por defecto
    precio = Decimal(precio)  # Convertir a Decimal para evitar errores
    precio_con_iva = precio * (1 + IVA_RATE)
    precio_final = precio_con_iva * (1 - DISCOUNT_RATE)
    return format_precio(precio_final)

# Función para limpiar el valor de Stock
def clean_stock(stock):
    return 0 if stock == 0 or abs(stock) < 1e-5 else (int(stock) if stock == int(stock) else round(stock, 2))

# Función para determinar la disponibilidad
def get_disponibilidad(stock):
    return "Entrega inmediata" if stock > 0 else "A pedido"

# Función para determinar el tipo de producto
def get_tipo_producto(sku):
    return "Alternativo" if sku.startswith("0/") and sku.endswith("B") else "Original"

@app.route('/')
def home():
    return '¡La API está viva y funcionando! 🚀'

# Endpoint para buscar artículos por OEM
@app.route('/api/search', methods=['GET'])
def search_by_oem():
    oem = request.args.get('oem')
    if not oem:
        return jsonify({'error': 'El parámetro "oem" es obligatorio'}), 400

    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        query = """
        SELECT Des_Articulo, Articulo, Existencias, PVP, Almacen
        FROM FHMABI_PR
        WHERE Articulo LIKE ?
        """
        cursor.execute(query, (oem + '%',))  # Busca coincidencias parciales
        rows = cursor.fetchall()

        if not rows:
            return jsonify({'message': 'No se encontraron resultados para el OEM proporcionado'}), 404

        data = []
        for row in rows:
            stock = clean_stock(row.Existencias)
            sku = row.Articulo
            precio_con_descuento = calcular_precio_con_descuento(row.PVP)

            data.append({
                'Nombre Producto': row.Des_Articulo,
                'SKU Interno de Cliente': sku,
                'Stock': stock,
                'Precio con IVA y Descuento': precio_con_descuento,
                'Tipo de Producto': get_tipo_producto(sku),
                'Disponibilidad': get_disponibilidad(stock),
                'Almacén': row.Almacen
            })

        cursor.close()
        conn.close()
        return jsonify(data)

    except pyodbc.Error as e:
        return jsonify({'error': f'Error de base de datos: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500

# Bloque para ejecutar la aplicación en producción
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Railway asigna este valor automáticamente
    app.run(host='0.0.0.0', port=port, debug=True)
