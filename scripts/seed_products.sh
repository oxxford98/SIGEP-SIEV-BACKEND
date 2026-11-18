#!/usr/bin/env bash
# Carga los 15 productos de ejemplo de «Inventario SIEV» por el API (POST /api/products/).
# Uso (Git Bash, desde back/):
#   ADMIN_EMAIL=admin@siev.local ADMIN_PASSWORD='...' bash scripts/seed_products.sh
# Requiere un usuario is_staff. Si un código ya existe, el API responde 400 y sigue con el siguiente.
# Margen, valor de inventario y estado los calcula el backend.
set -euo pipefail
API_URL="${API_URL:-http://127.0.0.1:8000}"
: "${ADMIN_EMAIL:?Define ADMIN_EMAIL}" "${ADMIN_PASSWORD:?Define ADMIN_PASSWORD}"

TOKEN=$(curl -sf -X POST "$API_URL/api/auth/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" | sed -E 's/.*"access":"([^"]+)".*/\1/')
[ -n "$TOKEN" ] || { echo "No se pudo iniciar sesión" >&2; exit 1; }

post() {
  curl -s -o /dev/null -w "%{http_code}  $1\n" -X POST "$API_URL/api/products/" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json; charset=utf-8" --data-binary @-
}

post 1000001 <<'JSON'
{
  "code": "1000001",
  "name": "Cable 12 rojo THHN/THWN-2",
  "category": "Cables y conductores",
  "brand": "Centelsa",
  "reference": "THHN/THWN-2 12 AWG",
  "unit": "Rollo 100 m",
  "stock": 4,
  "min_stock": 2,
  "unit_cost": 265000,
  "sale_price": 330000,
  "location": "Bodega – Estante A1",
  "supplier": "Por definir",
  "description": "Cable de cobre 12 AWG, aislamiento PVC con chaqueta de nylon, 600 V, 90 °C."
}
JSON

post 2000001 <<'JSON'
{
  "code": "2000001",
  "name": "Contactor 3P 25 A bobina 220 VAC",
  "category": "Control y protección",
  "brand": "Schneider Electric",
  "reference": "LC1D25M7",
  "unit": "Unidad",
  "stock": 6,
  "min_stock": 2,
  "unit_cost": 185000,
  "sale_price": 240000,
  "location": "Bodega – Estante B1",
  "supplier": "Por definir",
  "description": "Contactor tripolar TeSys D, 25 A en AC-3, bobina 220 VAC, contactos auxiliares 1NA+1NC."
}
JSON

post 2000002 <<'JSON'
{
  "code": "2000002",
  "name": "Guardamotor 9–12,5 A",
  "category": "Control y protección",
  "brand": "Siemens",
  "reference": "3RV2011-1KA10",
  "unit": "Unidad",
  "stock": 4,
  "min_stock": 2,
  "unit_cost": 240000,
  "sale_price": 310000,
  "location": "Bodega – Estante B1",
  "supplier": "Por definir",
  "description": "Guardamotor SIRIUS tamaño S00, rango 9–12,5 A, protección térmica y magnética."
}
JSON

post 2000003 <<'JSON'
{
  "code": "2000003",
  "name": "Breaker caja moldeada 3x100 A",
  "category": "Control y protección",
  "brand": "Schneider Electric",
  "reference": "EZC100N3100",
  "unit": "Unidad",
  "stock": 2,
  "min_stock": 1,
  "unit_cost": 430000,
  "sale_price": 560000,
  "location": "Bodega – Estante B2",
  "supplier": "Por definir",
  "description": "Interruptor EasyPact EZC100N, 3 polos, 100 A, para tableros de distribución."
}
JSON

post 2000004 <<'JSON'
{
  "code": "2000004",
  "name": "Pulsador paro de emergencia 40 mm",
  "category": "Control y protección",
  "brand": "Schneider Electric",
  "reference": "XB5AS8442",
  "unit": "Unidad",
  "stock": 10,
  "min_stock": 4,
  "unit_cost": 48000,
  "sale_price": 65000,
  "location": "Bodega – Estante B2",
  "supplier": "Por definir",
  "description": "Hongo rojo de 40 mm, enclavamiento girar para soltar, 1NC, montaje en 22 mm."
}
JSON

post 3000001 <<'JSON'
{
  "code": "3000001",
  "name": "PLC LOGO! 8 230RCE",
  "category": "Automatización",
  "brand": "Siemens",
  "reference": "6ED1052-1FB08-0BA1",
  "unit": "Unidad",
  "stock": 2,
  "min_stock": 1,
  "unit_cost": 680000,
  "sale_price": 860000,
  "location": "Bodega – Estante C1",
  "supplier": "Por definir",
  "description": "Módulo lógico con display, 8 entradas digitales y 4 salidas a relé, 115/230 V, puerto Ethernet."
}
JSON

post 3000002 <<'JSON'
{
  "code": "3000002",
  "name": "Variador de frecuencia 2 HP 220 V",
  "category": "Automatización",
  "brand": "Delta",
  "reference": "VFD015EL21A",
  "unit": "Unidad",
  "stock": 1,
  "min_stock": 1,
  "unit_cost": 950000,
  "sale_price": 1200000,
  "location": "Bodega – Estante C1",
  "supplier": "Por definir",
  "description": "Variador serie VFD-EL, 1,5 kW, entrada monofásica 220 V, salida trifásica para motor."
}
JSON

post 4000001 <<'JSON'
{
  "code": "4000001",
  "name": "Lámpara hermética LED 2x18 W IP65",
  "category": "Iluminación",
  "brand": "Sylvania",
  "reference": "Verificar con proveedor",
  "unit": "Unidad",
  "stock": 12,
  "min_stock": 6,
  "unit_cost": 88000,
  "sale_price": 118000,
  "location": "Bodega – Estante D1",
  "supplier": "Por definir",
  "description": "Luminaria hermética de 1,2 m con 2 tubos LED de 18 W, IP65, para zonas húmedas y de lavado."
}
JSON

post 4000002 <<'JSON'
{
  "code": "4000002",
  "name": "Luminaria de emergencia LED 2 faros",
  "category": "Iluminación",
  "brand": "Genérica",
  "reference": "Verificar con proveedor",
  "unit": "Unidad",
  "stock": 6,
  "min_stock": 2,
  "unit_cost": 75000,
  "sale_price": 99000,
  "location": "Bodega – Estante D1",
  "supplier": "Por definir",
  "description": "Luminaria de emergencia de 2 faros LED, batería recargable, autonomía aprox. 90 min, 110 V."
}
JSON

post 5000001 <<'JSON'
{
  "code": "5000001",
  "name": "Tubo EMT 3/4\" x 3 m",
  "category": "Canalización",
  "brand": "Colmena",
  "reference": "EMT 3/4\"",
  "unit": "Unidad",
  "stock": 40,
  "min_stock": 15,
  "unit_cost": 19000,
  "sale_price": 25000,
  "location": "Patio – Rack 1",
  "supplier": "Por definir",
  "description": "Tubo conduit metálico galvanizado de 3/4\", tramo de 3 m."
}
JSON

post 5000002 <<'JSON'
{
  "code": "5000002",
  "name": "Bandeja portacable tipo escalera 30 cm x 2,4 m",
  "category": "Canalización",
  "brand": "Nacional",
  "reference": "Escalera 30 x 10 cm",
  "unit": "Tramo",
  "stock": 8,
  "min_stock": 4,
  "unit_cost": 210000,
  "sale_price": 275000,
  "location": "Patio – Rack 2",
  "supplier": "Por definir",
  "description": "Bandeja galvanizada tipo escalera, ancho 30 cm, alto 10 cm, tramo de 2,4 m."
}
JSON

post 6000001 <<'JSON'
{
  "code": "6000001",
  "name": "Gabinete metálico 60x40x20 cm IP65",
  "category": "Tableros",
  "brand": "Rittal",
  "reference": "Verificar con proveedor",
  "unit": "Unidad",
  "stock": 2,
  "min_stock": 1,
  "unit_cost": 1150000,
  "sale_price": 1450000,
  "location": "Bodega – Piso",
  "supplier": "Por definir",
  "description": "Gabinete en lámina de acero con puerta, placa de montaje, IP65, para tableros de control."
}
JSON

post 7000001 <<'JSON'
{
  "code": "7000001",
  "name": "Varilla de puesta a tierra 5/8\" x 2,4 m",
  "category": "Puesta a tierra",
  "brand": "Nacional",
  "reference": "Copperweld 5/8\" x 2,4 m",
  "unit": "Unidad",
  "stock": 10,
  "min_stock": 4,
  "unit_cost": 80000,
  "sale_price": 105000,
  "location": "Patio – Rack 1",
  "supplier": "Por definir",
  "description": "Varilla de acero recubierta de cobre (copperweld) para sistemas de malla a tierra."
}
JSON

post 8000001 <<'JSON'
{
  "code": "8000001",
  "name": "Cinta aislante Super 33+",
  "category": "Consumibles",
  "brand": "3M",
  "reference": "Super 33+ 19 mm x 20 m",
  "unit": "Rollo",
  "stock": 30,
  "min_stock": 10,
  "unit_cost": 19000,
  "sale_price": 26000,
  "location": "Bodega – Estante E1",
  "supplier": "Por definir",
  "description": "Cinta vinílica negra de uso profesional, 600 V, resistente a humedad y rayos UV."
}
JSON

post 9000001 <<'JSON'
{
  "code": "9000001",
  "name": "Guantes dieléctricos clase 0",
  "category": "Dotación / EPP",
  "brand": "Salisbury",
  "reference": "Clase 0, talla 10",
  "unit": "Par",
  "stock": 3,
  "min_stock": 2,
  "unit_cost": 290000,
  "sale_price": 370000,
  "location": "Bodega – Estante E2",
  "supplier": "Por definir",
  "description": "Guantes de caucho clase 0 para trabajos hasta 1.000 V CA; usar con guante protector de cuero."
}
JSON
