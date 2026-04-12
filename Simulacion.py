from Sistema import Sistema
from Evento import Evento, TipoEvento
from Cliente import Cliente
import heapq
import random

class Simulacion:   # Clase para representar la simulación del sistema de colas
    def __init__(self, tiempo_total):
        self.tiempo_total = tiempo_total
        self.tiempo_actual = 0
        self.eventos = []
        self.sistema = Sistema()
        self.contador_eventos = 0  # Contador para asignar un ID único a cada evento
        self.contador_clientes = 0  # Contador para asignar un ID único a cada cliente

    def generar_tiempo_llegada(self):
        return random.randint(40, 60)  # Tiempo entre llegadas aleatorio entre 40 y 60 unidades de tiempo

    def generar_tiempo_servicio(self):
        return random.randint(45, 50)  # Tiempo de servicio aleatorio entre 45 y 50 unidades de tiempo

    def generar_tiempo_salida_servidor(self):
        return random.randint(55, 65)  # Tiempo hasta la próxima salida del servidor aleatorio entre 55 y 65 unidades de tiempo

    def generar_tiempo_llegada_servidor(self):
        return random.randint(25, 35)  # Tiempo hasta la próxima llegada del servidor aleatorio entre 25 y 35 unidades de tiempo
    
    def generar_tiempo_abandono(self):
        return 90 
    
    def generar_tiempo_llegada_a(self):
        return random.randint(80, 120)  # Tiempo entre llegadas de clientes tipo A aleatorio entre 80 y 120 unidades de tiempo

    def generar_tiempo_llegada_b(self):
        return random.randint(40, 60)  # Tiempo entre llegadas de clientes tipo B aleatorio entre 40 y 60 unidades de tiempo
    
    def generar_tiempo_abandono_a(self):
        return 120  # Tiempo hasta el abandono de clientes tipo A (si se implementa la distinción entre tipos de clientes)
    
    def generar_tiempo_abandono_b(self):
        return 90  # Tiempo hasta el abandono de clientes tipo B (si se implementa la distinción entre tipos de clientes)

    def inicio(self):
        # Generar el primer evento de llegada
        tiempo = self.generar_tiempo_llegada() # Generar el tiempo de llegada del primer cliente
        evento = Evento(TipoEvento.LLEGADA, tiempo)  # Crear el evento de llegada
        heapq.heappush(self.eventos, (tiempo, self.contador_eventos, evento))  # Agregar el evento a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        # Generar el primer evento de salida del servidor
        tiempo_salida_servidor = self.generar_tiempo_salida_servidor()  # Generar el tiempo hasta la primera salida del servidor
        evento_salida_servidor = Evento(TipoEvento.SALIDA_SERVIDOR, tiempo_salida_servidor)  # Crear el evento de salida del servidor
        heapq.heappush(self.eventos, (tiempo_salida_servidor, self.contador_eventos, evento_salida_servidor))  # Agregar el evento de salida del servidor a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        # Imprimir encabezados de la tabla
        print(f"|{'Hora actual':^15}|{'Próx. llegada':^17}|{'Próx. fin serv.':^20}|{'Hora Descanso':^15}|{'Hora Trabajo':^15}|{'Hora de abandono':^17}|{'PS':^7}|{'Cola':^7}|{'Servidor':^10}|{'Gráficamente':^15}|")
        print(
            f"|{'-'*15}|{'-'*17}|{'-'*20}|{'-'*15}|{'-'*15}|{'-'*17}|{'-'*7}|{'-'*7}|{'-'*10}|{'-'*15}|"
        )

    def inicio_prioridad(self):
        #Generar el primer evento de llegada para clientes tipo A y B
        tiempo_llegada_a = self.generar_tiempo_llegada_a()  # Generar el tiempo de llegada del primer cliente tipo A
        tiempo_llegada_b = self.generar_tiempo_llegada_b()  # Generar el tiempo de llegada del primer cliente tipo B
        evento_llegada_a = Evento(TipoEvento.LLEGADA_A, tiempo_llegada_a)  # Crear el evento de llegada para clientes tipo A
        evento_llegada_b = Evento(TipoEvento.LLEGADA_B, tiempo_llegada_b)  # Crear el evento de llegada para clientes tipo B
        heapq.heappush(self.eventos, (tiempo_llegada_a, self.contador_eventos, evento_llegada_a))  # Agregar el evento de llegada de clientes tipo A a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
        heapq.heappush(self.eventos, (tiempo_llegada_b, self.contador_eventos, evento_llegada_b))  # Agregar el evento de llegada de clientes tipo B a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        # Generar el primer evento de salida del servidor
        tiempo_salida_servidor = self.generar_tiempo_salida_servidor()  # Generar el tiempo hasta la primera salida del servidor
        evento_salida_servidor = Evento(TipoEvento.SALIDA_SERVIDOR, tiempo_salida_servidor)  # Crear el evento de salida del servidor
        heapq.heappush(self.eventos, (tiempo_salida_servidor, self.contador_eventos, evento_salida_servidor))  # Agregar el evento de salida del servidor a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        # Imprimir encabezados de la tabla
        print(f"|{'Hora actual':^15}|{'Próx. llegada A':^17}|{'Próx. llegada B':^17}|{'Próx. fin serv.':^20}|{'Hora Descanso':^15}|{'Hora Trabajo':^15}|{'Hora de abandono A':^20}|{'Hora de abandono B':^20}|{'PS':^7}|{'Cola A':^7}|{'Cola B':^7}|{'Servidor':^10}|{'Gráficamente':^15}|")
        print(
            f"|{'-'*15}|{'-'*17}|{'-'*17}|{'-'*20}|{'-'*15}|{'-'*15}|{'-'*20}|{'-'*20}|{'-'*7}|{'-'*7}|{'-'*7}|{'-'*10}|{'-'*15}|"
        )

    def procesar_llegada(self, evento):
        if not self.sistema.puesto_de_servicio and self.sistema.servidor:  # Si el puesto de servicio está desocupado y el servidor está disponible
            self.sistema.puesto_de_servicio = True  # Ocupamos el puesto de servicio
            tiempo_servicio = self.generar_tiempo_servicio()  # Generar el tiempo de servicio
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio)  # Crear el evento de fin de servicio
            self.sistema.tiempo_fin_servicio_actual = self.tiempo_actual + tiempo_servicio
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_servicio, self.contador_eventos, evento_fin))  # Agregar el evento de fin de servicio a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
        else:
            self.sistema.cola.append(Cliente(self.contador_clientes, self.tiempo_actual))  # Agregar el cliente a la cola
            self.contador_clientes += 1  # Incrementar el contador de clientes para asignar un ID único al próximo cliente

            # Generar el próximo evento de abandono para el cliente que acaba de llegar
            tiempo_abandono = self.generar_tiempo_abandono()  # Generar el tiempo hasta el abandono del cliente
            evento_abandono = Evento(TipoEvento.ABANDONO, self.tiempo_actual + tiempo_abandono)  # Crear el evento de abandono para el cliente que acaba de llegar
            evento_abandono.id_cliente = self.contador_clientes - 1  # Asignar el ID del cliente que acaba de llegar al evento de abandono correspondiente
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el evento de abandono a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        # Generar el próximo evento de llegada
        tiempo_llegada = self.generar_tiempo_llegada()  # Generar el tiempo de llegada del próximo cliente
        evento_llegada = Evento(TipoEvento.LLEGADA, self.tiempo_actual + tiempo_llegada)  # Crear el evento de llegada para el próximo cliente
        heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_llegada, self.contador_eventos, evento_llegada))  # Agregar el evento de llegada a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

    def procesar_llegada_a(self, evento):
        # Procesar la llegada de un cliente tipo A (si se implementa la distinción entre tipos de clientes)
        if not self.sistema.puesto_de_servicio and self.sistema.servidor:  # Si el puesto de servicio está desocupado y el servidor está disponible
            self.sistema.puesto_de_servicio = True  # Ocupamos el puesto de servicio
            tiempo_servicio = self.generar_tiempo_servicio()  # Generar el tiempo de servicio
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio)  # Crear el evento de fin de servicio
            self.sistema.tiempo_fin_servicio_actual = self.tiempo_actual + tiempo_servicio
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_servicio, self.contador_eventos, evento_fin))  # Agregar el evento de fin de servicio a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
        else:
            self.sistema.cola_A.append(Cliente(self.contador_clientes, self.tiempo_actual, "A"))  # Agregar el cliente tipo A a la cola de tipo A
            self.contador_clientes += 1  # Incrementar el contador de clientes para asignar un ID único al próximo cliente

            # Generar el próximo evento de abandono para el cliente tipo A que acaba de llegar
            tiempo_abandono = self.generar_tiempo_abandono_a()  # Generar el tiempo hasta el abandono del cliente tipo A
            evento_abandono = Evento(TipoEvento.ABANDONO, self.tiempo_actual + tiempo_abandono)  # Crear el evento de abandono para el cliente tipo A que acaba de llegar
            evento_abandono.id_cliente = self.contador_clientes - 1  # Asignar el ID del cliente tipo A que acaba de llegar al evento de abandono correspondiente
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el evento de abandono a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
        
        #Generar el próximo evento de llegada para clientes tipo A
        tiempo_llegada_a = self.generar_tiempo_llegada_a()  # Generar el tiempo hasta la próxima llegada de un cliente tipo A
        evento_llegada_a = Evento(TipoEvento.LLEGADA_A, self.tiempo_actual + tiempo_llegada_a)  # Crear el evento de llegada para clientes tipo A
        heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_llegada_a, self.contador_eventos, evento_llegada_a))  # Agregar el evento de llegada a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

    def procesar_llegada_b(self, evento):
        # Procesar la llegada de un cliente tipo B (si se implementa la distinción entre tipos de clientes)
        if not self.sistema.puesto_de_servicio and self.sistema.servidor:  # Si el puesto de servicio está desocupado y el servidor está disponible
            self.sistema.puesto_de_servicio = True  # Ocupamos el puesto de servicio
            tiempo_servicio = self.generar_tiempo_servicio()  # Generar el tiempo de servicio
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio)  # Crear el evento de fin de servicio
            self.sistema.tiempo_fin_servicio_actual = self.tiempo_actual + tiempo_servicio
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_servicio, self.contador_eventos, evento_fin))  # Agregar el evento de fin de servicio a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
        else:
            self.sistema.cola_B.append(Cliente(self.contador_clientes, self.tiempo_actual, "B"))  # Agregar el cliente tipo B a la cola de tipo B
            self.contador_clientes += 1  # Incrementar el contador de clientes para asignar un ID único al próximo cliente

            # Generar el próximo evento de abandono para el cliente tipo B que acaba de llegar
            tiempo_abandono = self.generar_tiempo_abandono_b()  # Generar el tiempo hasta el abandono del cliente tipo B
            evento_abandono = Evento(TipoEvento.ABANDONO, self.tiempo_actual + tiempo_abandono)  # Crear el evento de abandono para el cliente tipo B que acaba de llegar
            evento_abandono.id_cliente = self.contador_clientes - 1  # Asignar el ID del cliente tipo B que acaba de llegar al evento de abandono correspondiente
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el evento de abandono a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        #Generar el próximo evento de llegada para clientes tipo B
        tiempo_llegada_b = self.generar_tiempo_llegada_b()  # Generar el tiempo hasta la próxima llegada de un cliente tipo B
        evento_llegada_b = Evento(TipoEvento.LLEGADA_B, self.tiempo_actual + tiempo_llegada_b)  # Crear el evento de llegada para clientes tipo B
        heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_llegada_b, self.contador_eventos, evento_llegada_b))  # Agregar el evento de llegada a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento


    def procesar_fin_servicio(self, evento):
        if self.sistema.cola:  # Si hay clientes en la cola
            cliente_atendido = self.sistema.cola.pop(0)  # Sacar al primer cliente de la cola
            tiempo_servicio = self.generar_tiempo_servicio()  # Generar el tiempo de servicio para el siguiente cliente
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio)  # Crear el evento de fin de servicio para el siguiente cliente
            self.sistema.tiempo_fin_servicio_actual = self.tiempo_actual + tiempo_servicio # Actualizar el tiempo de fin de servicio actual con el tiempo del nuevo cliente que está siendo atendido
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_servicio, self.contador_eventos, evento_fin))  # Agregar el evento de fin de servicio a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

            # Si el cliente que acaba de ser atendido tenía un evento de abandono programado, se invalida ese evento ya que el cliente no abandonará el sistema. Usamos el ID del cliente que está siendo atendido para identificar su evento de abandono correspondiente y marcarlo como inválido
            for i in range(len(self.eventos)):
                if self.eventos[i][2].tipo == TipoEvento.ABANDONO and self.eventos[i][2].id_cliente == cliente_atendido.id:  # Si el evento es de abandono y su ID de cliente coincide con el ID del cliente que estaba siendo atendido
                    self.eventos[i][2].valido = False  # Marcar el evento de abandono como inválido
                    break

            # Si quedan clientes en la cola después de sacar al cliente que acaba de ser atendido, se programa un nuevo evento de abandono para el siguiente cliente en la cola
            if self.sistema.cola:
                tiempo_abandono = self.generar_tiempo_abandono()  # Generar el tiempo hasta el abandono del siguiente cliente
                tiempo_llegada_cliente = self.sistema.cola[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente en la cola
                evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente en la cola
                evento_abandono.id_cliente = self.sistema.cola[0].id  # Asignar el ID del siguiente cliente en la cola al evento de abandono correspondiente
                heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
                self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
        else:
            self.sistema.puesto_de_servicio = False  # Si no hay clientes en la cola, el puesto de servicio queda desocupado
            self.sistema.tiempo_fin_servicio_actual = None  # Reiniciar el tiempo de fin de servicio actual ya que no hay cliente siendo atendido

    def procesar_fin_servicio_con_prioridad(self, evento): #Se tendrá en cuenta que hay clientes de tipo A y B, y se dará prioridad a los clientes de tipo A al momento de sacar un cliente de la cola para atenderlo
        if self.sistema.cola_A:  # Si hay clientes de tipo A en la cola
            cliente_atendido = self.sistema.cola_A.pop(0)  # Sacar al primer cliente de tipo A de la cola
            cola_salida = "A"  # Variable para indicar que el cliente atendido es de tipo A

        elif self.sistema.cola_B:  # Si no hay clientes de tipo A pero sí hay clientes de tipo B en la cola
            cliente_atendido = self.sistema.cola_B.pop(0)  # Sacar al primer cliente de tipo B de la cola
            cola_salida = "B"  # Variable para indicar que el cliente atendido es de tipo B

        else:
            self.sistema.puesto_de_servicio = False  # Si no hay clientes en ninguna de las colas, el puesto de servicio queda desocupado
            self.sistema.tiempo_fin_servicio_actual = None  # Reiniciar el tiempo de fin de servicio actual ya que no hay cliente siendo atendido
            return

        tiempo_servicio = self.generar_tiempo_servicio()  # Generar el tiempo de servicio para el siguiente cliente
        evento_fin = Evento(TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio)  # Crear el evento de fin de servicio para el siguiente cliente
        self.sistema.tiempo_fin_servicio_actual = self.tiempo_actual + tiempo_servicio # Actualizar el tiempo de fin de servicio actual con el tiempo del nuevo cliente que está siendo atendido
        heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_servicio, self.contador_eventos, evento_fin))  # Agregar el evento de fin de servicio a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        # Si el cliente que acaba de ser atendido tenía un evento de abandono programado, se invalida ese evento ya que el cliente no abandonará el sistema. Usamos el ID del cliente que estaba siendo atendido para identificar su evento de abandono correspondiente y marcarlo como inválido
        for i in range(len(self.eventos)):
            if self.eventos[i][2].tipo == TipoEvento.ABANDONO and self.eventos[i][2].id_cliente == cliente_atendido.id:  # Si el evento es de abandono y su ID de cliente coincide con el ID del cliente que estaba siendo atendido
                self.eventos[i][2].valido = False  # Marcar el evento de abandono como inválido
                break
        
        # Si quedan clientes en la cola después de sacar al cliente que acaba de ser atendido, se programa un nuevo evento de abandono para el siguiente
        if cola_salida == "A" and self.sistema.cola_A:  # Si el cliente atendido era de tipo A y quedan clientes de tipo A en la cola
            tiempo_abandono = self.generar_tiempo_abandono_a()  # Generar el tiempo hasta el abandono del siguiente cliente de tipo A
            tiempo_llegada_cliente = self.sistema.cola_A[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente de tipo A en la cola
            evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente de tipo A en la cola
            evento_abandono.id_cliente = self.sistema.cola_A[0].id  # Asignar el ID del siguiente cliente de tipo A en la cola al evento de abandono correspondiente
            heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
        elif cola_salida == "B" and self.sistema.cola_B:  # Si el cliente atendido era de tipo B y quedan clientes de tipo B en la cola
            tiempo_abandono = self.generar_tiempo_abandono_b()  # Generar el tiempo hasta el abandono del siguiente cliente de tipo B
            tiempo_llegada_cliente = self.sistema.cola_B[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente de tipo B en la cola
            evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente de tipo B en la cola
            evento_abandono.id_cliente = self.sistema.cola_B[0].id  # Asignar el ID del siguiente cliente de tipo B en la cola al evento de abandono correspondiente
            heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

    def obtener_proxima_llegada(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.LLEGADA:
                return evento[0]  # Retorna el tiempo de la próxima llegada
        return ""  # Si no hay eventos de llegada programados
    
    def obtener_proxima_llegada_a(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.LLEGADA_A:
                return evento[0]  # Retorna el tiempo de la próxima llegada de un cliente tipo A
        return ""  # Si no hay eventos de llegada de clientes tipo A programados
    
    def obtener_proxima_llegada_b(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.LLEGADA_B:
                return evento[0]  # Retorna el tiempo de la próxima llegada de un cliente tipo B
        return ""  # Si no hay eventos de llegada de clientes tipo B programados

    def obtener_proximo_fin_servicio(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.FIN_SERVICIO:
                return evento[0]  # Retorna el tiempo del próximo fin de servicio
        return ""  # Si no hay eventos de fin de servicio programados

    def procesar_salida_servidor(self, evento):
        self.sistema.servidor = False  # El servidor sale, por lo que se marca como no disponible
        # Si el servidor sale mientras un cliente está siendo atendido, se invalida el evento de fin de servicio actual
        if self.sistema.tiempo_fin_servicio_actual is not None:
            for i in range(len(self.eventos)):
                if self.eventos[i][2].tipo == TipoEvento.FIN_SERVICIO and self.eventos[i][0] == self.sistema.tiempo_fin_servicio_actual:
                    self.eventos[i][2].valido = False  # Marcar el evento de fin de servicio como inválido
                    break
            # Calcular el tiempo restante de servicio para el cliente actual
            self.sistema.tiempo_restante_servicio_actual = self.sistema.tiempo_fin_servicio_actual - self.tiempo_actual

        # Generar el próximo evento de llegada del servidor
        tiempo_llegada_servidor = self.generar_tiempo_llegada_servidor()  # Generar el tiempo hasta la próxima llegada del servidor
        evento_llegada_servidor = Evento(TipoEvento.LLEGADA_SERVIDOR, self.tiempo_actual + tiempo_llegada_servidor)  # Crear el evento de llegada del servidor
        heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_llegada_servidor, self.contador_eventos, evento_llegada_servidor))  # Agregar el evento de llegada del servidor a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

    def procesar_llegada_servidor(self, evento):
        self.sistema.servidor = True  # El servidor llega, por lo que se marca como disponible
        # Si el servidor llega y hay un cliente esperando en el puesto de servicio, se programa un nuevo evento de fin de servicio para ese cliente
        if self.sistema.puesto_de_servicio and self.sistema.tiempo_restante_servicio_actual is not None:
            tiempo_fin_servicio = self.tiempo_actual + self.sistema.tiempo_restante_servicio_actual  # Calcular el nuevo tiempo de fin de servicio para el cliente actual
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, tiempo_fin_servicio)  # Crear un nuevo evento de fin de servicio para el cliente actual
            self.sistema.tiempo_fin_servicio_actual = tiempo_fin_servicio  # Actualizar el tiempo de fin de servicio actual con el nuevo tiempo calculado
            heapq.heappush(self.eventos, (tiempo_fin_servicio, self.contador_eventos, evento_fin))  # Agregar el nuevo evento de fin de servicio a la cola de eventos
            self.sistema.tiempo_restante_servicio_actual = None  # Reiniciar el tiempo restante de servicio actual ya que el cliente está siendo atendido nuevamente

        # Si el servidor llega y el puesto de servicio está desocupado pero hay clientes en la cola, se programa un nuevo evento de fin de servicio para el siguiente cliente en la cola
        elif not self.sistema.puesto_de_servicio and self.sistema.cola:
            self.sistema.puesto_de_servicio = True  # El siguiente cliente de la cola ocupa el puesto de servicio
            cliente_atendido = self.sistema.cola.pop(0)  # Sacar al primer cliente de la cola
            tiempo_servicio = self.generar_tiempo_servicio()  # Generar el tiempo de servicio para el siguiente cliente
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio)  # Crear un nuevo evento de fin de servicio para el siguiente cliente
            self.sistema.tiempo_fin_servicio_actual = self.tiempo_actual + tiempo_servicio  # Actualizar el tiempo de fin de servicio actual con el nuevo tiempo calculado
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_servicio, self.contador_eventos, evento_fin))  # Agregar el nuevo evento de fin de servicio a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
            self.sistema.tiempo_restante_servicio_actual = None  # Reiniciar el tiempo restante de servicio actual ya que el cliente está siendo atendido

            # Si el cliente que acaba de ser atendido tenía un evento de abandono programado, se invalida ese evento ya que el cliente no abandonará el sistema, usando su ID
            for i in range(len(self.eventos)):
                if self.eventos[i][2].tipo == TipoEvento.ABANDONO and self.eventos[i][2].id_cliente == cliente_atendido.id:  # Si el evento es de abandono y su ID de cliente coincide con el ID del cliente que estaba siendo atendido
                    self.eventos[i][2].valido = False  # Marcar el evento de abandono como inválido
                    break
            
            # Si quedan clientes en la cola después de sacar al cliente que acaba de ser atendido, se programa un nuevo evento de abandono para el siguiente cliente en la cola
            if self.sistema.cola:
                tiempo_abandono = self.generar_tiempo_abandono()  # Generar el tiempo hasta el abandono del siguiente cliente
                tiempo_llegada_cliente = self.sistema.cola[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente en la cola
                evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente en la cola
                evento_abandono.id_cliente = self.sistema.cola[0].id  # Asignar el ID del siguiente cliente en la cola al evento de abandono correspondiente
                heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
                self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        # Generar el próximo evento de salida del servidor
        tiempo_salida_servidor = self.generar_tiempo_salida_servidor()  # Generar el tiempo hasta la próxima salida del servidor
        evento_salida_servidor = Evento(TipoEvento.SALIDA_SERVIDOR, self.tiempo_actual + tiempo_salida_servidor)  # Crear el evento de salida del servidor
        heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_salida_servidor, self.contador_eventos, evento_salida_servidor))  # Agregar el evento de salida del servidor a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

    def procesar_llegada_servidor_con_prioridad(self, evento): #Se tendrá en cuenta que hay clientes de tipo A y B, y se dará prioridad a los clientes de tipo A al momento de sacar un cliente de la cola para atenderlo cuando el servidor llegue
        self.sistema.servidor = True  # El servidor llega, por lo que se marca como disponible
        # Si el servidor llega y hay un cliente esperando en el puesto de servicio, se programa un nuevo evento de fin de servicio para ese cliente
        if self.sistema.puesto_de_servicio and self.sistema.tiempo_restante_servicio_actual is not None:
            tiempo_fin_servicio = self.tiempo_actual + self.sistema.tiempo_restante_servicio_actual  # Calcular el nuevo tiempo de fin de servicio para el cliente actual
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, tiempo_fin_servicio)  # Crear un nuevo evento de fin de servicio para el cliente actual
            self.sistema.tiempo_fin_servicio_actual = tiempo_fin_servicio  # Actualizar el tiempo de fin de servicio actual con el nuevo tiempo calculado
            heapq.heappush(self.eventos, (tiempo_fin_servicio, self.contador_eventos, evento_fin))  # Agregar el nuevo evento de fin de servicio a la cola de eventos
            self.sistema.tiempo_restante_servicio_actual = None  # Reiniciar el tiempo restante de servicio actual ya que el cliente está siendo atendido nuevamente

        # Si el servidor llega y el puesto de servicio está desocupado pero hay clientes en las colas, se programa un nuevo evento de fin de servicio para el siguiente cliente en la cola, dando prioridad a los clientes de tipo A
        elif not self.sistema.puesto_de_servicio and (self.sistema.cola_A or self.sistema.cola_B):
            if self.sistema.cola_A:  # Si hay clientes de tipo A en la cola, se atiende al siguiente cliente de tipo A
                self.sistema.puesto_de_servicio = True  # El siguiente cliente de la cola ocupa el puesto de servicio
                cliente_atendido = self.sistema.cola_A.pop(0)  # Sacar al primer cliente de tipo A de la cola
                cola_salida = "A"  # Variable para indicar que el cliente atendido es de tipo A
            else:  # Si no hay clientes de tipo A pero sí hay clientes de tipo B en la cola, se atiende al siguiente cliente de tipo B
                self.sistema.puesto_de_servicio = True  # El siguiente cliente de la cola ocupa el puesto de servicio
                cliente_atendido = self.sistema.cola_B.pop(0)  # Sacar al primer cliente de tipo B de la cola
                cola_salida = "B"  # Variable para indicar que el cliente atendido es de tipo B

            # Generar el evento de fin de servicio para el cliente que acaba de ser atendido
            tiempo_servicio = self.generar_tiempo_servicio()  # Generar el tiempo de servicio para el siguiente cliente
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio)  # Crear un nuevo evento de fin de servicio para el siguiente cliente
            self.sistema.tiempo_fin_servicio_actual = self.tiempo_actual + tiempo_servicio  # Actualizar el tiempo de fin de servicio actual con el nuevo tiempo calculado
            heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_servicio, self.contador_eventos, evento_fin))  # Agregar el nuevo evento de fin de servicio a la cola de eventos
            self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
            self.sistema.tiempo_restante_servicio_actual = None  # Reiniciar el tiempo restante de servicio actual ya que el cliente está siendo atendido

            # Si el cliente que acaba de ser atendido tenía un evento de abandono programado, se invalida ese evento ya que el cliente no abandonará el sistema, usando su ID
            for i in range(len(self.eventos)):
                if self.eventos[i][2].tipo == TipoEvento.ABANDONO and self.eventos[i][2].id_cliente == cliente_atendido.id:  # Si el evento es de abandono y su ID de cliente coincide con el ID del cliente que estaba siendo atendido
                    self.eventos[i][2].valido = False  # Marcar el evento de abandono como inválido
                    break
            
            # Si quedan clientes en las colas después de sacar al cliente que acaba de ser atendido, se programa un nuevo evento de abandono para el siguiente cliente en la cola
            if cola_salida == "A" and self.sistema.cola_A:  # Si el cliente atendido era de tipo A y quedan clientes de tipo A en la cola
                tiempo_abandono = self.generar_tiempo_abandono_a()  # Generar el tiempo hasta el abandono del siguiente cliente de tipo A
                tiempo_llegada_cliente = self.sistema.cola_A[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente de tipo A en la cola
                evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente de tipo A en la cola
                evento_abandono.id_cliente = self.sistema.cola_A[0].id  # Asignar el ID del siguiente cliente de tipo A en la cola al evento de abandono correspondiente
                heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
                self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

            elif cola_salida == "B" and self.sistema.cola_B:  # Si el cliente atendido era de tipo B y quedan clientes de tipo B en la cola
                tiempo_abandono = self.generar_tiempo_abandono_b()  # Generar el tiempo hasta el abandono del siguiente cliente de tipo B
                tiempo_llegada_cliente = self.sistema.cola_B[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente de tipo B en la cola
                evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente de tipo B en la cola
                evento_abandono.id_cliente = self.sistema.cola_B[0].id  # Asignar el ID del siguiente cliente de tipo B en la cola al evento de abandono correspondiente
                heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
                self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        # Generar el próximo evento de salida del servidor
        tiempo_salida_servidor = self.generar_tiempo_salida_servidor()  # Generar el tiempo hasta la próxima salida del servidor
        evento_salida_servidor = Evento(TipoEvento.SALIDA_SERVIDOR, self.tiempo_actual + tiempo_salida_servidor)  # Crear el evento de salida del servidor
        heapq.heappush(self.eventos, (self.tiempo_actual + tiempo_salida_servidor, self.contador_eventos, evento_salida_servidor))  # Agregar el evento de salida del servidor a la cola de eventos
        self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

    def obtener_proximo_descanso(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.SALIDA_SERVIDOR:
                return evento[0]  # Retorna el tiempo de la próxima salida del servidor
        return ""  # Si no hay eventos de salida del servidor programados   

    def obtener_proximo_trabajo(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.LLEGADA_SERVIDOR:
                return evento[0]  # Retorna el tiempo de la próxima llegada del servidor
        return ""  # Si no hay eventos de llegada del servidor programados
    
    def procesar_abandono(self, evento):
        if self.sistema.cola:  # Si hay clientes en la cola
            cliente_abandono = self.sistema.cola.pop(0)  # Sacar al primer cliente de la cola (el que va a abandonar)

            # Si quedan clientes, hay que programar un nuevo evento de abandono para el siguiente cliente en la cola
            if self.sistema.cola:
                tiempo_abandono = self.generar_tiempo_abandono()  # Generar el tiempo hasta el abandono del siguiente cliente
                tiempo_llegada_cliente = self.sistema.cola[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente en la cola
                evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente en la cola
                heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
                self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento
    
    def procesar_abandono_con_prioridad(self, evento): #Se tendrá en cuenta si el abandono es de un cliente de tipo A o B, y se eliminará al primer cliente de la cola correspondiente
        #Verificar si el cliente es de tipo A o B sacándolo del evento de abandono
        if self.sistema.cola_A and evento.id_cliente in [cliente.id for cliente in self.sistema.cola_A]:  # Si hay clientes de tipo A en la cola y el ID del cliente que abandona coincide con el ID de algún cliente de tipo A en la cola
            cliente_abandono = next(cliente for cliente in self.sistema.cola_A if cliente.id == evento.id_cliente)  # Obtener el cliente de tipo A que abandona
            self.sistema.cola_A.remove(cliente_abandono)  # Eliminar al cliente de tipo A que abandona de la cola de tipo A

            # Si quedan clientes de tipo A, hay que programar un nuevo evento de abandono para el siguiente cliente de tipo A en la cola
            if self.sistema.cola_A:
                tiempo_abandono = self.generar_tiempo_abandono_a()  # Generar el tiempo hasta el abandono del siguiente cliente de tipo A
                tiempo_llegada_cliente = self.sistema.cola_A[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente de tipo A en la cola
                evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente de tipo A en la cola
                evento_abandono.id_cliente = self.sistema.cola_A[0].id  # Asignar el ID del siguiente cliente de tipo A en la cola al evento de abandono correspondiente
                heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
                self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento

        elif self.sistema.cola_B and evento.id_cliente in [cliente.id for cliente in self.sistema.cola_B]:  # Si hay clientes de tipo B en la cola y el ID del cliente que abandona coincide con el ID de algún cliente de tipo B en la cola
            cliente_abandono = next(cliente for cliente in self.sistema.cola_B if cliente.id == evento.id_cliente)  # Obtener el cliente de tipo B que abandona
            self.sistema.cola_B.remove(cliente_abandono)  # Eliminar al cliente de tipo B que abandona de la cola de tipo B

            # Si quedan clientes de tipo B, hay que programar un nuevo evento de abandono para el siguiente cliente de tipo B en la cola
            if self.sistema.cola_B:
                tiempo_abandono = self.generar_tiempo_abandono_b()  # Generar el tiempo hasta el abandono del siguiente cliente de tipo B
                tiempo_llegada_cliente = self.sistema.cola_B[0].hora_llegada  # Obtener la hora de llegada del siguiente cliente de tipo B en la cola
                evento_abandono = Evento(TipoEvento.ABANDONO, tiempo_llegada_cliente + tiempo_abandono)  # Crear un nuevo evento de abandono para el siguiente cliente de tipo B en la cola
                evento_abandono.id_cliente = self.sistema.cola_B[0].id  # Asignar el ID del siguiente cliente de tipo B en la cola al evento de abandono correspondiente
                heapq.heappush(self.eventos, (tiempo_llegada_cliente + tiempo_abandono, self.contador_eventos, evento_abandono))  # Agregar el nuevo evento de abandono a la cola de eventos
                self.contador_eventos += 1  # Incrementar el contador de eventos para asignar un ID único al próximo evento


    def obtener_proximo_abandono(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.ABANDONO:
                return evento[0]  # Retorna el tiempo del próximo abandono
        return ""  # Si no hay eventos de abandono programados
    
    def obtener_proximo_abandono_a(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.ABANDONO and evento[2].id_cliente in [cliente.id for cliente in self.sistema.cola_A]:  # Si el evento es de abandono y su ID de cliente coincide con el ID de algún cliente de tipo A en la cola
                return evento[0]  # Retorna el tiempo del próximo abandono de un cliente tipo A
        return ""  # Si no hay eventos de abandono de clientes tipo A programados
    
    def obtener_proximo_abandono_b(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.ABANDONO and evento[2].id_cliente in [cliente.id for cliente in self.sistema.cola_B]:  # Si el evento es de abandono y su ID de cliente coincide con el ID de algún cliente de tipo B en la cola
                return evento[0]  # Retorna el tiempo del próximo abandono de un cliente tipo B
        return ""  # Si no hay eventos de abandono de clientes tipo B programados

    def ejecutar(self):
        # Ejecuta el próximo evento
        while self.eventos and self.tiempo_actual < self.tiempo_total:  # Mientras haya eventos en la cola y el tiempo actual sea menor al tiempo total de la simulación

            evento = heapq.heappop(self.eventos)
            if not evento[2].valido:  # Si el evento ha sido invalidado, se ignora y se continúa con el siguiente evento
                continue

            self.tiempo_actual = evento[0]  # Actualizar el tiempo actual al tiempo del evento
            if evento[2].tipo == TipoEvento.LLEGADA:
                self.procesar_llegada(evento[2])  # Procesar el evento de llegada
            elif evento[2].tipo == TipoEvento.FIN_SERVICIO:
                self.procesar_fin_servicio(evento[2])  # Procesar el evento de fin de servicio
            elif evento[2].tipo == TipoEvento.SALIDA_SERVIDOR:
                self.procesar_salida_servidor(evento[2])  # Procesar el evento de salida del servidor
            elif evento[2].tipo == TipoEvento.LLEGADA_SERVIDOR:
                self.procesar_llegada_servidor(evento[2])  # Procesar el evento de llegada del servidor
            elif evento[2].tipo == TipoEvento.ABANDONO:
                self.procesar_abandono(evento[2])  # Procesar el evento de abandono

            # Imprimir el estado actual del sistema después de procesar el evento
            grafico = "⧇" if self.sistema.puesto_de_servicio else "▢" 
            grafico += "D" if self.sistema.servidor else " "  
            if len(self.sistema.cola) > 0:
                grafico += "O" * len(self.sistema.cola)  # Agregar representación gráfica de los clientes en la cola

            print(
             f"|{self.tiempo_actual:^15}|{self.obtener_proxima_llegada():^17}|{self.obtener_proximo_fin_servicio():^20}|{self.obtener_proximo_descanso():^15}|{self.obtener_proximo_trabajo():^15}|{self.obtener_proximo_abandono():^17}|{self.sistema.puesto_de_servicio:^7}|{len(self.sistema.cola):^7}|{self.sistema.servidor:^10}|{grafico:^15}|"
             )
            
    def ejecutar_con_prioridad(self):
        # Ejecuta el próximo evento, dando prioridad a los clientes de tipo A sobre los de tipo B
        while self.eventos and self.tiempo_actual < self.tiempo_total:  # Mientras haya eventos en la cola y el tiempo actual sea menor al tiempo total de la simulación

            evento = heapq.heappop(self.eventos)
            if not evento[2].valido:  # Si el evento ha sido invalidado, se ignora y se continúa con el siguiente evento
                continue

            self.tiempo_actual = evento[0]  # Actualizar el tiempo actual al tiempo del evento
            if evento[2].tipo == TipoEvento.LLEGADA_A:
                self.procesar_llegada_a(evento[2])  # Procesar el evento de llegada de un cliente tipo A
            elif evento[2].tipo == TipoEvento.LLEGADA_B:
                self.procesar_llegada_b(evento[2])  # Procesar el evento de llegada de un cliente tipo B
            elif evento[2].tipo == TipoEvento.FIN_SERVICIO:
                self.procesar_fin_servicio_con_prioridad(evento[2])  # Procesar el evento de fin de servicio dando prioridad a los clientes de tipo A
            elif evento[2].tipo == TipoEvento.SALIDA_SERVIDOR:
                self.procesar_salida_servidor(evento[2])  # Procesar el evento de salida del servidor
            elif evento[2].tipo == TipoEvento.LLEGADA_SERVIDOR:
                self.procesar_llegada_servidor_con_prioridad(evento[2])  # Procesar el evento de llegada del servidor dando prioridad a los clientes de tipo A
            elif evento[2].tipo == TipoEvento.ABANDONO:
                self.procesar_abandono_con_prioridad(evento[2])  # Procesar el evento de abandono dando prioridad a los clientes de tipo A

            # Imprimir el estado actual del sistema después de procesar el evento
            grafico = "⧇" if self.sistema.puesto_de_servicio else "▢" 
            grafico += "D" if self.sistema.servidor else " "  
            if len(self.sistema.cola_A) > 0:
                grafico += "A" * len(self.sistema.cola_A)  # Agregar representación gráfica de los clientes de tipo A en la cola
            if len(self.sistema.cola_B) > 0:
                grafico += "B" * len(self.sistema.cola_B)  # Agregar representación gráfica de los clientes de tipo B en la cola
            
            print(
             f"|{self.tiempo_actual:^15}|{self.obtener_proxima_llegada_a():^17}|{self.obtener_proxima_llegada_b():^17}|{self.obtener_proximo_fin_servicio():^20}|{self.obtener_proximo_descanso():^15}|{self.obtener_proximo_trabajo():^15}|{self.obtener_proximo_abandono_a():^20}|{self.obtener_proximo_abandono_b():^20}|{self.sistema.puesto_de_servicio:^7}|{len(self.sistema.cola_A):^7}|{len(self.sistema.cola_B):^7}|{self.sistema.servidor:^10}|{grafico:^15}|"
             )
