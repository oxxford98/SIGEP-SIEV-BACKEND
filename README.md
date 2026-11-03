# SIGEP-SIEV-BACKEND

Backend REST desarrollado con Django y Django REST Framework. El proyecto utiliza SQLite como base de datos local y autenticación JWT.

## Requisitos

- Python 3.10 o superior
- `pip`

## Instalación y ejecución en Windows

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# Instalar las dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# Aplicar las migraciones
python manage.py migrate

# Crear el usuario administrador
python manage.py createsuperuser

# Iniciar el servidor de desarrollo
python manage.py runserver
```

El servidor estará disponible en <http://127.0.0.1:8000/>. Para detenerlo, pulsa `Ctrl+C` en la terminal.

Si PowerShell impide activar el entorno virtual, permite la ejecución de scripts solo para la sesión actual y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

## Instalación y ejecución en macOS o Linux

Desde la carpeta del proyecto:

```bash
# Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar las dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# Aplicar las migraciones y crear el usuario administrador
python manage.py migrate
python manage.py createsuperuser

# Iniciar el servidor de desarrollo
python manage.py runserver
```

## Rutas disponibles

Con el servidor en ejecución:

- Administración: <http://127.0.0.1:8000/admin/>
- Documentación Swagger: <http://127.0.0.1:8000/docs/>
- Documentación ReDoc: <http://127.0.0.1:8000/redocs/>
- API: <http://127.0.0.1:8000/api/>

La base de datos SQLite (`db.sqlite3`) se crea en la carpeta del proyecto al aplicar las migraciones.

## Pruebas

Con el entorno virtual activado, ejecuta:

```bash
python manage.py test
```
