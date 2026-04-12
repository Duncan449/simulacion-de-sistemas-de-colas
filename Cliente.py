class Cliente:
    def __init__(self, id, hora_llegada, tipo):
        self.id = id  # Identificador del cliente
        self.hora_llegada = hora_llegada  # Hora en la que el cliente llega al sistema
        self.tipo = tipo  # Tipo de cliente (A o B)