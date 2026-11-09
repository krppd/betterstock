from __future__ import annotations

from models.usuario import Usuario
from repositories.usuario_repositorio import UsuarioRepositorio


class Autenticacion:
    LARGO_MINIMO_PASSWORD = 4

    def __init__(self, usuarios: UsuarioRepositorio) -> None:
        self._usuarios = usuarios
        self._usuario_actual: Usuario | None = None

    @property
    def usuario_actual(self) -> Usuario | None:
        return self._usuario_actual

    def inicializar(self, sembrar_iniciales: bool = True) -> None:
        self._usuarios.inicializar()

    def hay_usuarios(self) -> bool:
        return bool(self._usuarios.listar())

    def crear_usuario(self, nombre: str, password: str,
                      permiso: str = Usuario.PERMISO_ADMIN) -> Usuario:
        """Nuevo usuario; ValueError si el nombre ya existe."""
        usuario = Usuario.crear(nombre, password, permiso)
        self._usuarios.agregar(usuario)
        self._usuario_actual = usuario
        return usuario

    def iniciar_sesion(self, nombre: str, password: str) -> bool:
        usuario = self._usuarios.buscar(nombre)
        if usuario is None or not usuario.verificar_password(password):
            return False

        if usuario.necesita_rehash():
            usuario.actualizar_password(password)
            self._usuarios.guardar(usuario)

        self._usuario_actual = usuario
        return True

    def cerrar_sesion(self) -> None:
        self._usuario_actual = None

    def cambiar_password(self, password_actual: str,
                         password_nueva: str) -> None:
        usuario = self._usuario_actual
        if usuario is None:
            raise ValueError("No hay una sesión iniciada.")
        if not usuario.verificar_password(password_actual):
            raise ValueError("La contraseña actual no es correcta.")
        if len(password_nueva) < self.LARGO_MINIMO_PASSWORD:
            raise ValueError(
                "La contraseña debe tener al menos "
                f"{self.LARGO_MINIMO_PASSWORD} caracteres.")
        usuario.actualizar_password(password_nueva)
        self._usuarios.guardar(usuario)
