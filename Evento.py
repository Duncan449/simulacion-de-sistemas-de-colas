from enum import Enum


class TipoEvento(Enum):  # Enum para representar los tipos de eventos
    LLEGADA = 1
    FIN_SERVICIO = 2
    LLEGADA_SERVIDOR = 3
    SALIDA_SERVIDOR = 4
    ABANDONO = 5
    LLEGADA_A = 6
    LLEGADA_B = 7


class Evento:   # Clase para representar un evento en la simulación
    def __init__(self, tipo, tiempo):
        self.tipo = tipo
        self.tiempo = tiempo
        self.valido = True  # Atributo para marcar si el evento es válido o ha sido invalidado
        self.id_cliente = None  # Atributo para almacenar el ID del cliente asociado al evento (si fuera necesario)
