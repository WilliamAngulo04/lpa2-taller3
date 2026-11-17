# API de Música

[![CI](https://github.com/WilliamAngulo04/lpa2-taller3/actions/workflows/ci.yml/badge.svg)](https://github.com/WilliamAngulo04/lpa2-taller3/actions/workflows/ci.yml)

## Datos del Estudiante

| Campo       | Valor                            |
|-------------|----------------------------------|
| Nombre      | William Q. Angulo A.             |
| Código      | _(tu código estudiantil)_        |
| Usuario Git | [WilliamAngulo04](https://github.com/WilliamAngulo04) |
| Curso       | Lenguajes de Programación Avanzada 2 (LPA2) |

Una [API RESTful](https://aws.amazon.com/es/what-is/restful-api/) para gestionar usuarios, canciones y favoritos. Desarrollada con [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/) y [Pydantic](https://docs.pydantic.dev/).

## Descripción

Esta API permite administrar:
- **Usuarios**: crear y gestionar perfiles de usuarios.
- **Canciones**: agregar, actualizar y eliminar canciones con sus metadatos.
- **Favoritos**: gestionar las canciones favoritas de cada usuario.

El proyecto incluye una interfaz de documentación interactiva generada automáticamente con [Swagger](https://swagger.io/) disponible en el *endpoint* `/docs`.

## Estructura del Proyecto

```
lpa2-taller3
├── README.md                 # Este archivo, documentación completa del proyecto
├── .env                      # Variables de entorno (copiar desde .env.example)
├── .env.example              # Plantilla de variables de entorno
├── .gitignore                # Archivos y directorios a ignorar por Git
├── .pre-commit-config.yaml   # Hooks de pre-commit (ruff + pytest)
├── .github/workflows/ci.yml  # GitHub Actions: ruff + pytest
├── main.py                   # Script principal para ejecutar la aplicación
├── musica.db                 # Base de Datos
├── musica_api
│   ├── __init__.py           # Inicialización del módulo
│   ├── config.py             # Configuración por entorno (Pydantic Settings)
│   ├── database.py           # Engine, creación de tablas y sesión
│   ├── models.py             # Modelos SQLModel y esquemas con validación
│   ├── paginacion.py         # Mejora: paginación de listados
│   ├── logging_config.py     # Mejora: sistema de registro (logging)
│   ├── seguridad.py          # Mejora: OAuth2 + JWT (bcrypt, token, usuario actual)
│   └── routers               # Endpoints: usuarios, canciones, favoritos
├── pyproject.toml            # Configuración de pytest y ruff
├── requirements.txt          # Dependencias del proyecto
├── scripts
│   └── datos_iniciales.sql   # 5 usuarios y 10 canciones para DBeaver
├── tests
│   ├── test_api.py           # Pruebas de la API
│   └── test_utils.py         # Pruebas de utilidades
└── utils.py                  # Funciones de utilidad
```
## Modelo de Datos

1. **Usuario**:
   - id: Identificador único
   - nombre: Nombre del usuario
   - correo: Correo electrónico (único)
   - fecha_registro: Fecha de registro

2. **Canción**:
   - id: Identificador único
   - titulo: Título de la canción
   - artista: Artista o intérprete
   - album: Álbum al que pertenece
   - duracion: Duración en segundos
   - año: Año de lanzamiento
   - genero: Género musical
   - fecha_creacion: Fecha de creación del registro

3. **Favorito**:
   - id: Identificador único
   - id_usuario: ID del usuario (clave foránea)
   - id_cancion: ID de la canción (clave foránea)
   - fecha_marcado: Fecha en que se marcó como favorito

## Instalación

1. Clona este repositorio:

   ```bash
   git clone https://github.com/WilliamAngulo04/lpa2-taller3.git
   cd lpa2-taller3
   ```

2. Crea y activa un entorno virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux / macOS
   .\venv\Scripts\activate       # Windows (PowerShell)
   ```

   En PowerShell la ruta debe empezar con `.\`; si la activación está bloqueada, se puede usar el Python del entorno sin activarlo: `.\venv\Scripts\python.exe -m uvicorn main:app --reload`.

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Ajusta las variables de entorno, copiando `.env.example` a `.env` y editándolo

5. Instala los hooks de pre-commit:

   ```bash
   pre-commit install
   ```

## Ejecución

1. Ejecuta la aplicación:

   ```bash
   uvicorn main:app --reload
   ```

2. Accede a la aplicación:
   - API: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - Documentación *Swagger UI*: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Documentación *ReDoc*: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Pruebas y calidad de código

```bash
pytest                       # pruebas automatizadas
ruff check .                 # linter
ruff format .                # formatter
pre-commit run --all-files   # todos los hooks
```

Son 67 pruebas (usuarios, canciones, favoritos, integración, validación, paginación, logging y autenticación). Las pruebas que no son de autenticación simulan un usuario autenticado con `dependency_overrides`.

En cada `push` y `pull request` a `main`, GitHub Actions ejecuta ruff y pytest.

## Uso de la API

> Los listados (`GET` de colecciones y búsqueda) son **paginados**: aceptan
> `?pagina=1&tamaño=10` y responden con `total`, `pagina`, `tamaño`, `paginas` e `items`.
>
> Los `GET` son públicos. Los `POST`, `PUT` y `DELETE` exigen el encabezado
> `Authorization: Bearer <token>` (si falta o es inválido responden `401`).

### Autenticación

- **Registrarse**: `POST /api/auth/registro` con `{"nombre", "correo", "password"}`
- **Iniciar sesión (OAuth2)**: `POST /api/auth/token` (formulario con `username` = correo y `password`) → `{"access_token", "token_type": "bearer"}`
- **Usuario autenticado**: `GET /api/auth/me`

En Swagger UI (`/docs`) el botón **Authorize** usa este mismo flujo.

### Usuarios

- **Listar usuarios**: `GET /api/usuarios`
- **Crear usuario**: `POST /api/usuarios`
- **Obtener usuario**: `GET /api/usuarios/{id}`
- **Actualizar usuario**: `PUT /api/usuarios/{id}`
- **Eliminar usuario**: `DELETE /api/usuarios/{id}`

### Canciones

- **Listar canciones**: `GET /api/canciones`
- **Crear canción**: `POST /api/canciones`
- **Obtener canción**: `GET /api/canciones/{id}`
- **Actualizar canción**: `PUT /api/canciones/{id}`
- **Eliminar canción**: `DELETE /api/canciones/{id}`
- **Buscar canciones**: `GET /api/canciones/buscar?titulo=value&artista=value&genero=value`

### Favoritos

- **Listar favoritos**: `GET /api/favoritos`
- **Marcar favorito**: `POST /api/favoritos`
- **Obtener favorito**: `GET /api/favoritos/{id}`
- **Eliminar favorito**: `DELETE /api/favoritos/{id}`
- **Listar favoritos de usuario**: `GET /api/usuarios/{id}/favoritos`
- **Marcar favorito específico**: `POST /api/usuarios/{id_usuario}/favoritos/{id_cancion}`
- **Eliminar favorito específico**: `DELETE /api/usuarios/{id_usuario}/favoritos/{id_cancion}`

## Desarrollo del Taller

1. Ajustar este `README.md` con los datos del Estudiante

2. Utilizando [DBeaver](https://dbeaver.io/), adiciona 5 usuarios y 10 canciones, directo a las tablas.

3. Adicionar `pre-commit` y `workflow` de GitHub Actions para **ruff** *linter* y *formatter*, y para **pytest**.

4. Busca todos los comentarios `# TODO` y `# FIXME`, realiza los ajustes necesarios, y ejecuta un `commit` por cada uno. Usa Pydantic para la validación de datos.

5. Prueba el funcionamiento del API, desde la documentación *Swagger UI* o *ReDoc*.

6. Desarrolla las pruebas automatizadas para verificar el funcionamiento correcto de la API.

7. Implementar dos (2) de las sugerencias que se presentan a continuación.

## Mejoras Implementadas

### 1. Paginación (sugerencia 2)

- Módulo [`musica_api/paginacion.py`](musica_api/paginacion.py) con la dependencia `ParametrosPaginacion` y el modelo genérico `Pagina[T]`.
- Aplicada a: `/api/usuarios`, `/api/canciones`, `/api/canciones/buscar`, `/api/favoritos` y `/api/usuarios/{id}/favoritos`.
- Usa `OFFSET`/`LIMIT` en SQL (no carga toda la tabla en memoria) y un `COUNT` para el total.
- Tamaño por defecto y máximo configurables (`PAGE_SIZE_DEFAULT`, `PAGE_SIZE_MAX`).

### 2. Registro / logging (sugerencia 5)

- Módulo [`musica_api/logging_config.py`](musica_api/logging_config.py): salida a consola y a archivo con rotación (1 MB × 5 archivos).
- Middleware que registra cada request: método, ruta, código de estado, duración y cliente; agrega el encabezado `X-Process-Time-Ms`.
- Nivel según el resultado: `INFO` (2xx/3xx), `WARNING` (4xx), `ERROR` (5xx).
- Manejadores de errores que registran la traza completa sin exponerla al cliente.
- Eventos de negocio (creación/eliminación de usuarios, canciones y favoritos).
- Configurable con `LOG_LEVEL` y `LOG_FILE`.

### 3. Autenticación con OAuth2 + JWT (sugerencia 1)

Agregada para el login y registro del frontend del [lpa2-taller4](https://github.com/WilliamAngulo04/lpa2-taller4).

- Módulo [`musica_api/seguridad.py`](musica_api/seguridad.py): flujo de contraseña de OAuth2 (`OAuth2PasswordBearer`), contraseñas cifradas con bcrypt y tokens JWT firmados con `SECRET_KEY` (`ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Router [`musica_api/routers/auth.py`](musica_api/routers/auth.py) con registro, token y perfil.
- La dependencia `get_usuario_actual` protege todos los endpoints de escritura; las lecturas siguen públicas.
- Columna nueva `usuario.password_hash`, agregada automáticamente a bases existentes al iniciar. Los usuarios cargados con DBeaver no tienen contraseña y no pueden iniciar sesión; se crean cuentas nuevas con el registro.
- 11 pruebas nuevas en `tests/test_api.py` (`TestAutenticacion`).

## Sugerencias de Mejora

1. **Autenticación y autorización**: Implementar JWT o OAuth2 para proteger los endpoints y asociar los usuarios automáticamente con sus favoritos.

2. **Paginación**: Añadir soporte para paginación en las listas de canciones, usuarios y favoritos para mejorar el rendimiento con grandes volúmenes de datos.

3. **Base de datos en producción**: Migrar a una base de datos más robusta como PostgreSQL o MySQL para entornos de producción.

4. **Docker**: Contenerizar la aplicación para facilitar su despliegue en diferentes entornos.

5. **Registro (logging)**: Implementar un sistema de registro más completo para monitorear errores y uso de la API.

6. **Caché**: Añadir caché para mejorar la velocidad de respuesta en consultas frecuentes.

7. **Estadísticas de uso**: Implementar un sistema de seguimiento para analizar qué canciones son más populares y sugerir recomendaciones basadas en preferencias similares.

8. **Subida de archivos**: Permitir la subida de archivos de audio y gestionar su almacenamiento en un servicio como S3 o similar.
