"""
Clase Cliente — Almacena y valida datos del cliente.
"""

class Cliente:
    def __init__(self, id_cliente=None, nombre="", empresa="",
                 nit="", direccion="", telefono="", email=""):
        self.id_cliente = id_cliente
        self.nombre    = nombre
        self.empresa   = empresa
        self.nit       = nit
        self.direccion = direccion
        self.telefono  = telefono
        self.email     = email

    def __str__(self):
        return (
            f"ID      : {self.id_cliente}\n"
            f"Nombre  : {self.nombre}\n"
            f"Empresa : {self.empresa}\n"
            f"NIT     : {self.nit}\n"
            f"Dir.    : {self.direccion}\n"
            f"Tel.    : {self.telefono}\n"
            f"Email   : {self.email}"
        )

    def to_dict(self):
        return {
            "id_cliente": self.id_cliente,
            "nombre":     self.nombre,
            "empresa":    self.empresa,
            "nit":        self.nit,
            "direccion":  self.direccion,
            "telefono":   self.telefono,
            "email":      self.email,
        }
