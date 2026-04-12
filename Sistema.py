class Sistema:          # Clase para representar el sistema de colas
    def __init__(self):
        self.puesto_de_servicio = False  #false = desocupado, true = ocupado
        self.cola_A = []  # Lista para representar la cola de clientes de tipo A
        self.cola_B = []  # Lista para representar la cola de clientes de tipo B
        self.cola = []  # Lista para representar la cola general de clientes general (si no hay distinción entre tipos)
        self.servidor = True #false = servidor cerrado o no disponible, true = servidor abierto o presente
        self.tiempo_fin_servicio_actual = None # Variable para almacenar el tiempo de fin de servicio del cliente actual
        self.tiempo_restante_servicio_actual = None # Variable para almacenar el tiempo restante de servicio del cliente actual en caso de que el servidor salga durante su atención
