from enum import Enum


class TipoEvento(Enum):  # Enum para representar los tipos de eventos
    LLEGADA = 1
    FIN_SERVICIO = 2
    LLEGADA_SERVIDOR = 3
    SALIDA_SERVIDOR = 4
    ABANDONO = 5
    LLEGADA_A = 6
    LLEGADA_B = 7
    LLEGADA_AL_PS = 8
    #Eventos modo múltiples PS (cola compartida)
    FIN_SERVICIO_PS = 9       # Fin de servicio en un PS específico (lleva id_ps)
    SALIDA_SERVIDOR_PS = 10   # Servidor de un PS específico se ausenta (lleva id_ps)
    LLEGADA_SERVIDOR_PS = 11  # Servidor de un PS específico regresa (lleva id_ps)
    LLEGADA_AL_PS_PS = 12     # Cliente llega al PS tras caminar por zona de seguridad (lleva id_ps)

class Evento:   # Clase para representar un evento en la simulación
    def __init__(self, tipo, tiempo):
        self.tipo = tipo
        self.tiempo = tiempo
        self.valido = True  # Atributo para marcar si el evento es válido o ha sido invalidado
        self.id_cliente = None  # Atributo para almacenar el ID del cliente asociado al evento (si fuera necesario)
        self.id_ps = None         # ID del PS asociado al evento (para modo multi-PS)