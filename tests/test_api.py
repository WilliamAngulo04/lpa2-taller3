"""
Tests para la API de Música.
Pruebas unitarias y de integración usando pytest.
"""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from main import app
from musica_api.database import get_session
from musica_api.models import Cancion, Favorito, Usuario
from musica_api.seguridad import get_usuario_actual

# =============================================================================
# CONFIGURACIÓN DE FIXTURES
# =============================================================================


# Fixture para crear una base de datos en memoria para testing
@pytest.fixture(name="session")
def session_fixture():
    """
    Crea una sesión de base de datos en memoria para cada test.
    Se limpia automáticamente después de cada test.
    """
    # Crear engine en memoria (SQLite)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)

    # Crear sesión
    with Session(engine) as session:
        yield session


# Fixture para cliente de pruebas
@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Crea un cliente de pruebas de FastAPI con la sesión de test.
    """

    # Override de la dependencia get_session
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    # Los endpoints de escritura exigen token: se simula un usuario autenticado
    app.dependency_overrides[get_usuario_actual] = lambda: Usuario(
        id=0, nombre="Autenticado", correo="auth@example.com"
    )
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Fixture para cliente sin autenticación simulada (pruebas de OAuth2)
@pytest.fixture(name="client_auth")
def client_auth_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Fixture para crear usuarios de prueba
@pytest.fixture(name="usuario_test")
def usuario_test_fixture(session: Session):
    """
    Crea un usuario de prueba en la base de datos.
    """
    usuario = Usuario(nombre="Usuario Test", correo="test@example.com")
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


# Fixture para crear canciones de prueba
@pytest.fixture(name="cancion_test")
def cancion_test_fixture(session: Session):
    """
    Crea una cancion de prueba en la base de datos.
    """
    cancion = Cancion(
        titulo="Canción Test",
        artista="Artista Test",
        album="Álbum Test",
        duracion=200,
        año=2020,
        genero="Rock",
    )
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion


# =============================================================================
# TESTS DE USUARIOS
# =============================================================================


class TestUsuarios:
    """Tests para los endpoints de usuarios."""

    def test_listar_usuarios(self, client: TestClient, usuario_test: Usuario):
        """Test para GET /api/usuarios"""
        response = client.get("/api/usuarios")
        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) == 1
        assert data[0]["correo"] == usuario_test.correo

    def test_crear_usuario(self, client: TestClient):
        """Test para POST /api/usuarios"""
        response = client.post(
            "/api/usuarios", json={"nombre": "Ana Pérez", "correo": "Ana@Mail.com"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["nombre"] == "Ana Pérez"
        assert data["correo"] == "ana@mail.com"
        assert "fecha_registro" in data

    def test_crear_usuario_correo_duplicado(
        self, client: TestClient, usuario_test: Usuario
    ):
        """Test para verificar que no se permiten correos duplicados"""
        response = client.post(
            "/api/usuarios", json={"nombre": "Otro", "correo": usuario_test.correo}
        )
        assert response.status_code == 409

    def test_obtener_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para GET /api/usuarios/{id}"""
        response = client.get(f"/api/usuarios/{usuario_test.id}")
        assert response.status_code == 200
        assert response.json()["nombre"] == usuario_test.nombre

    def test_obtener_usuario_no_existe(self, client: TestClient):
        """Test para verificar error 404 con usuario inexistente"""
        response = client.get("/api/usuarios/999")
        assert response.status_code == 404

    def test_actualizar_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para PUT /api/usuarios/{id}"""
        response = client.put(
            f"/api/usuarios/{usuario_test.id}", json={"nombre": "Nombre Nuevo"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Nombre Nuevo"
        assert data["correo"] == usuario_test.correo

    def test_actualizar_usuario_correo_duplicado(
        self, client: TestClient, usuario_test: Usuario
    ):
        """No se puede cambiar el correo a uno que ya usa otro usuario"""
        otro = client.post(
            "/api/usuarios", json={"nombre": "Otro", "correo": "otro@example.com"}
        ).json()
        response = client.put(
            f"/api/usuarios/{otro['id']}", json={"correo": usuario_test.correo}
        )
        assert response.status_code == 409

    def test_eliminar_usuario(self, client: TestClient, usuario_test: Usuario):
        """Test para DELETE /api/usuarios/{id}"""
        response = client.delete(f"/api/usuarios/{usuario_test.id}")
        assert response.status_code == 204
        assert client.get(f"/api/usuarios/{usuario_test.id}").status_code == 404


# =============================================================================
# TESTS DE CANCIONES
# =============================================================================


class TestCanciones:
    """Tests para los endpoints de canciones."""

    def test_listar_canciones(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones"""
        response = client.get("/api/canciones")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    def test_crear_cancion(self, client: TestClient):
        """Test para POST /api/canciones"""
        response = client.post(
            "/api/canciones",
            json={
                "titulo": "Bohemian Rhapsody",
                "artista": "Queen",
                "album": "A Night at the Opera",
                "duracion": 355,
                "año": 1975,
                "genero": "Rock",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["titulo"] == "Bohemian Rhapsody"
        assert data["año"] == 1975

    def test_obtener_cancion(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones/{id}"""
        response = client.get(f"/api/canciones/{cancion_test.id}")
        assert response.status_code == 200
        assert response.json()["titulo"] == cancion_test.titulo

    def test_obtener_cancion_no_existe(self, client: TestClient):
        """Test para verificar error 404 con canción inexistente"""
        assert client.get("/api/canciones/999").status_code == 404

    def test_actualizar_cancion(self, client: TestClient, cancion_test: Cancion):
        """Test para PUT /api/canciones/{id}"""
        response = client.put(
            f"/api/canciones/{cancion_test.id}", json={"genero": "Pop", "duracion": 180}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["genero"] == "Pop"
        assert data["duracion"] == 180
        assert data["titulo"] == cancion_test.titulo

    def test_eliminar_cancion(self, client: TestClient, cancion_test: Cancion):
        """Test para DELETE /api/canciones/{id}"""
        response = client.delete(f"/api/canciones/{cancion_test.id}")
        assert response.status_code == 204
        assert client.get(f"/api/canciones/{cancion_test.id}").status_code == 404

    def test_buscar_canciones(self, client: TestClient, cancion_test: Cancion):
        """Test para GET /api/canciones/buscar"""
        response = client.get("/api/canciones/buscar", params={"titulo": "test"})
        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) == 1
        assert data[0]["id"] == cancion_test.id

        response = client.get("/api/canciones/buscar", params={"titulo": "nada"})
        assert response.json()["items"] == []

    def test_buscar_canciones_multiples_filtros(self, client: TestClient):
        """Test para búsqueda con múltiples parámetros"""
        canciones = [
            ("Song A", "Shakira", "Pop"),
            ("Song B", "Shakira", "Rock"),
            ("Song C", "Juanes", "Rock"),
        ]
        for titulo, artista, genero in canciones:
            client.post(
                "/api/canciones",
                json={
                    "titulo": titulo,
                    "artista": artista,
                    "duracion": 200,
                    "año": 2010,
                    "genero": genero,
                },
            )

        response = client.get(
            "/api/canciones/buscar", params={"artista": "shakira", "genero": "rock"}
        )
        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) == 1
        assert data[0]["titulo"] == "Song B"


# =============================================================================
# TESTS DE PAGINACIÓN
# =============================================================================


class TestPaginacion:
    """Tests para la paginación de los listados (mejora)."""

    @pytest.fixture(autouse=True)
    def crear_canciones(self, session: Session):
        for i in range(1, 26):
            session.add(
                Cancion(
                    titulo=f"Canción {i}",
                    artista="Artista",
                    duracion=100 + i,
                    año=2000,
                    genero="Pop",
                )
            )
        session.commit()

    def test_pagina_por_defecto(self, client: TestClient):
        data = client.get("/api/canciones").json()
        assert data["total"] == 25
        assert data["pagina"] == 1
        assert data["tamaño"] == 10
        assert data["paginas"] == 3
        assert len(data["items"]) == 10
        assert data["items"][0]["titulo"] == "Canción 1"

    def test_ultima_pagina(self, client: TestClient):
        data = client.get("/api/canciones", params={"pagina": 3, "tamaño": 10}).json()
        assert len(data["items"]) == 5
        assert data["items"][-1]["titulo"] == "Canción 25"

    def test_pagina_fuera_de_rango(self, client: TestClient):
        data = client.get("/api/canciones", params={"pagina": 10}).json()
        assert data["items"] == []
        assert data["total"] == 25

    def test_busqueda_paginada(self, client: TestClient):
        params = {"artista": "artista", "pagina": 2, "tamaño": 20}
        data = client.get("/api/canciones/buscar", params=params).json()
        assert data["total"] == 25
        assert len(data["items"]) == 5

    @pytest.mark.parametrize("params", [{"pagina": 0}, {"tamaño": 0}, {"tamaño": 101}])
    def test_parametros_invalidos(self, client: TestClient, params: dict):
        assert client.get("/api/canciones", params=params).status_code == 422


# =============================================================================
# TESTS DE FAVORITOS
# =============================================================================


class TestFavoritos:
    """Tests para los endpoints de favoritos."""

    def test_listar_favoritos(self, client: TestClient):
        """Test para GET /api/favoritos"""
        response = client.get("/api/favoritos")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_crear_favorito(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para POST /api/favoritos"""
        response = client.post(
            "/api/favoritos",
            json={"id_usuario": usuario_test.id, "id_cancion": cancion_test.id},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id_usuario"] == usuario_test.id
        assert data["id_cancion"] == cancion_test.id
        assert "fecha_marcado" in data

    def test_crear_favorito_referencias_inexistentes(
        self, client: TestClient, usuario_test: Usuario
    ):
        """No se puede marcar favorito con canción o usuario inexistente"""
        response = client.post(
            "/api/favoritos", json={"id_usuario": usuario_test.id, "id_cancion": 999}
        )
        assert response.status_code == 404

    def test_crear_favorito_duplicado(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para verificar que no se permiten favoritos duplicados"""
        datos = {"id_usuario": usuario_test.id, "id_cancion": cancion_test.id}
        assert client.post("/api/favoritos", json=datos).status_code == 201
        assert client.post("/api/favoritos", json=datos).status_code == 409

    def test_obtener_favorito(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Test para GET /api/favoritos/{id}"""
        favorito = Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id)
        session.add(favorito)
        session.commit()
        response = client.get(f"/api/favoritos/{favorito.id}")
        assert response.status_code == 200
        assert response.json()["id_cancion"] == cancion_test.id

    def test_eliminar_favorito(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Test para DELETE /api/favoritos/{id}"""
        favorito = Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id)
        session.add(favorito)
        session.commit()
        response = client.delete(f"/api/favoritos/{favorito.id}")
        assert response.status_code == 204
        assert client.get(f"/api/favoritos/{favorito.id}").status_code == 404

    def test_marcar_favorito_usuario(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para POST /api/usuarios/{id}/favoritos/{id_cancion}"""
        url = f"/api/usuarios/{usuario_test.id}/favoritos/{cancion_test.id}"
        response = client.post(url)
        assert response.status_code == 201
        assert response.json()["id_usuario"] == usuario_test.id
        assert client.post(url).status_code == 409

    def test_eliminar_favorito_usuario(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Test para DELETE /api/usuarios/{id}/favoritos/{id_cancion}"""
        url = f"/api/usuarios/{usuario_test.id}/favoritos/{cancion_test.id}"
        client.post(url)
        assert client.delete(url).status_code == 204
        assert client.delete(url).status_code == 404

    def test_listar_favoritos_usuario(
        self,
        client: TestClient,
        session: Session,
        usuario_test: Usuario,
        cancion_test: Cancion,
    ):
        """Test para GET /api/usuarios/{id}/favoritos"""
        session.add(Favorito(id_usuario=usuario_test.id, id_cancion=cancion_test.id))
        session.commit()
        response = client.get(f"/api/usuarios/{usuario_test.id}/favoritos")
        assert response.status_code == 200
        data = response.json()["items"]
        assert len(data) == 1
        assert data[0]["id_cancion"] == cancion_test.id

    def test_eliminar_cancion_elimina_favoritos(
        self, client: TestClient, usuario_test: Usuario, cancion_test: Cancion
    ):
        """Al eliminar una canción se eliminan sus favoritos"""
        client.post(f"/api/usuarios/{usuario_test.id}/favoritos/{cancion_test.id}")
        client.delete(f"/api/canciones/{cancion_test.id}")
        assert client.get("/api/favoritos").json()["items"] == []


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================


class TestIntegracion:
    """Tests de integración que prueban flujos completos."""

    def test_flujo_completo(self, client: TestClient):
        """Test que verifica el flujo completo de la aplicación"""
        # 1. Crear usuario
        usuario = client.post(
            "/api/usuarios", json={"nombre": "Laura", "correo": "laura@mail.com"}
        ).json()

        # 2. Crear canción
        cancion = client.post(
            "/api/canciones",
            json={
                "titulo": "La Bicicleta",
                "artista": "Carlos Vives",
                "duracion": 227,
                "año": 2016,
                "genero": "Vallenato",
            },
        ).json()

        # 3. Marcar como favorito
        response = client.post(
            f"/api/usuarios/{usuario['id']}/favoritos/{cancion['id']}"
        )
        assert response.status_code == 201

        # 4. Verificar que aparece en favoritos del usuario
        url = f"/api/usuarios/{usuario['id']}/favoritos"
        favoritos = client.get(url).json()["items"]
        assert [f["id_cancion"] for f in favoritos] == [cancion["id"]]

    def test_root_y_health(self, client: TestClient):
        """Los endpoints informativos responden correctamente"""
        root = client.get("/")
        assert root.status_code == 200
        assert root.json()["documentacion"]["swagger"] == "/docs"
        health = client.get("/health")
        assert health.status_code == 200
        assert "status" in health.json()


# =============================================================================
# TESTS DE VALIDACIÓN
# =============================================================================


class TestValidacion:
    """Tests para validaciones de datos."""

    def test_email_invalido(self, client: TestClient):
        """Test para verificar validación de email"""
        for correo in ["sin-arroba", "a@b", "@dominio.com", "a b@c.com"]:
            response = client.post(
                "/api/usuarios", json={"nombre": "Test", "correo": correo}
            )
            assert response.status_code == 422, correo

    def test_año_cancion_invalido(self, client: TestClient):
        """Test para verificar validación de año"""
        base = {"titulo": "X", "artista": "Y", "duracion": 100, "genero": "Pop"}
        for año in [1800, 3000]:
            response = client.post("/api/canciones", json={**base, "año": año})
            assert response.status_code == 422, año

    def test_duracion_invalida(self, client: TestClient):
        """La duración debe ser positiva"""
        response = client.post(
            "/api/canciones",
            json={
                "titulo": "X",
                "artista": "Y",
                "duracion": 0,
                "año": 2000,
                "genero": "Pop",
            },
        )
        assert response.status_code == 422

    def test_campos_requeridos(self, client: TestClient):
        """Test para verificar que los campos requeridos son obligatorios"""
        assert client.post("/api/usuarios", json={}).status_code == 422
        assert client.post("/api/usuarios", json={"nombre": "Solo"}).status_code == 422
        response = client.post("/api/canciones", json={"titulo": "Solo título"})
        assert response.status_code == 422
        campos = {e["loc"][-1] for e in response.json()["detail"]}
        assert {"artista", "duracion", "año", "genero"} <= campos


# =============================================================================
# TESTS DE LOGGING
# =============================================================================


class TestLogging:
    """Tests para el sistema de registro (mejora)."""

    @pytest.fixture(autouse=True)
    def capturar_logs(self, caplog: pytest.LogCaptureFixture):
        # El logger de la app no propaga a root; se habilita para caplog
        logger = logging.getLogger("musica_api")
        logger.propagate = True
        caplog.set_level(logging.INFO, logger="musica_api")
        yield
        logger.propagate = False

    def test_registra_requests(self, client: TestClient, caplog):
        response = client.get("/api/usuarios")
        assert "X-Process-Time-Ms" in response.headers
        assert any("GET /api/usuarios -> 200" in r.message for r in caplog.records)

    def test_registra_errores_como_warning(self, client: TestClient, caplog):
        client.get("/api/usuarios/999")
        registro = next(r for r in caplog.records if "/api/usuarios/999" in r.message)
        assert registro.levelno == logging.WARNING

    def test_registra_eventos(self, client: TestClient, caplog):
        client.post("/api/usuarios", json={"nombre": "Log", "correo": "log@x.com"})
        assert any("Usuario creado" in r.message for r in caplog.records)


# =============================================================================
# TESTS DE AUTENTICACIÓN (OAuth2 + JWT)
# =============================================================================


class TestAutenticacion:
    """Registro, inicio de sesión y protección de endpoints de escritura."""

    REGISTRO = {"nombre": "Ana", "correo": "Ana@Mail.com", "password": "secreta123"}

    def iniciar_sesion(self, client: TestClient, password: str = "secreta123"):
        return client.post(
            "/api/auth/token", data={"username": "ana@mail.com", "password": password}
        )

    def test_registro(self, client_auth: TestClient):
        response = client_auth.post("/api/auth/registro", json=self.REGISTRO)
        assert response.status_code == 201
        data = response.json()
        assert data["correo"] == "ana@mail.com"
        assert "password" not in data and "password_hash" not in data

    def test_registro_correo_duplicado(self, client_auth: TestClient):
        client_auth.post("/api/auth/registro", json=self.REGISTRO)
        response = client_auth.post("/api/auth/registro", json=self.REGISTRO)
        assert response.status_code == 409

    def test_registro_password_corta(self, client_auth: TestClient):
        datos = {**self.REGISTRO, "password": "corta"}
        response = client_auth.post("/api/auth/registro", json=datos)
        assert response.status_code == 422

    def test_password_se_guarda_cifrada(self, client_auth: TestClient, session):
        client_auth.post("/api/auth/registro", json=self.REGISTRO)
        usuario = session.exec(
            select(Usuario).where(Usuario.correo == "ana@mail.com")
        ).one()
        assert usuario.password_hash.startswith("$2")
        assert "secreta123" not in usuario.password_hash

    def test_login_y_perfil(self, client_auth: TestClient):
        client_auth.post("/api/auth/registro", json=self.REGISTRO)
        response = self.iniciar_sesion(client_auth)
        assert response.status_code == 200
        token = response.json()
        assert token["token_type"] == "bearer"
        perfil = client_auth.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        assert perfil.status_code == 200
        assert perfil.json()["correo"] == "ana@mail.com"

    def test_login_password_incorrecta(self, client_auth: TestClient):
        client_auth.post("/api/auth/registro", json=self.REGISTRO)
        response = self.iniciar_sesion(client_auth, password="otra-clave")
        assert response.status_code == 401

    def test_login_usuario_sin_password(
        self, client_auth: TestClient, usuario_test: Usuario
    ):
        """Los usuarios cargados sin contraseña (DBeaver) no pueden iniciar sesión."""
        response = client_auth.post(
            "/api/auth/token",
            data={"username": usuario_test.correo, "password": "cualquiera"},
        )
        assert response.status_code == 401

    def test_perfil_token_invalido(self, client_auth: TestClient):
        response = client_auth.get(
            "/api/auth/me", headers={"Authorization": "Bearer no-es-un-jwt"}
        )
        assert response.status_code == 401

    def test_escritura_sin_token(self, client_auth: TestClient):
        response = client_auth.post(
            "/api/canciones",
            json={
                "titulo": "X",
                "artista": "Y",
                "duracion": 100,
                "año": 2020,
                "genero": "Pop",
            },
        )
        assert response.status_code == 401

    def test_lectura_publica(self, client_auth: TestClient):
        assert client_auth.get("/api/canciones").status_code == 200

    def test_escritura_con_token(self, client_auth: TestClient):
        client_auth.post("/api/auth/registro", json=self.REGISTRO)
        token = self.iniciar_sesion(client_auth).json()["access_token"]
        response = client_auth.post(
            "/api/canciones",
            json={
                "titulo": "X",
                "artista": "Y",
                "duracion": 100,
                "año": 2020,
                "genero": "Pop",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
