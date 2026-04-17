from Sistema import Sistema
from Evento import Evento, TipoEvento
from Cliente import Cliente
import heapq
import random


class Simulacion:  # Clase para representar la simulación del sistema de colas
    def __init__(self, tiempo_total, config):
        self.tiempo_total = tiempo_total
        self.config = config  # Configuración de la simulación (tipos de clientes, abandono, descanso, etc.)
        self.tiempo_actual = 0
        self.eventos = []
        self.sistema = Sistema()
        self.contador_eventos = 0  # Contador para asignar un ID único a cada evento
        self.contador_clientes = 0  # Contador para asignar un ID único a cada cliente

        # Métricas de la simulación 
        self.clientes_atendidos = 0  # Cantidad de clientes que completaron su servicio
        self.clientes_atendidos_a = 0  
        self.clientes_atendidos_b = 0  
        self.clientes_abandonaron = 0  # Cantidad de clientes que abandonaron la cola
        self.clientes_abandonaron_a = 0  
        self.clientes_abandonaron_b = 0  
        self.tiempos_espera = []  # Lista de tiempos de espera de cada cliente atendido (para calcular promedio al final)
        self.tiempos_espera_a = []  
        self.tiempos_espera_b = []  
        self.tiempo_servidor_ocupado = 0  # Tiempo total que el PS estuvo ocupado
        self.tiempo_servidor_ausente = 0  # Tiempo total que el servidor estuvo ausente
        self._tiempo_inicio_servicio = None  # Auxiliar para calcular tiempo ocupado
        self._tiempo_inicio_ausencia = None  # Auxiliar para calcular tiempo ausente

    # Generadores de tiempo 

    def generar_tiempo_llegada(self):
        minimo = self.config["llegada_min"]
        maximo = self.config["llegada_max"]
        return random.randint(minimo, maximo) if minimo != maximo else minimo
    

    def generar_tiempo_llegada_a(self):
        minimo = self.config["llegada_a_min"]
        maximo = self.config["llegada_a_max"]
        return random.randint(minimo, maximo) if minimo != maximo else minimo

    def generar_tiempo_llegada_b(self):
        minimo = self.config["llegada_b_min"]
        maximo = self.config["llegada_b_max"]
        return random.randint(minimo, maximo) if minimo != maximo else minimo

    def generar_tiempo_servicio(self):
        minimo = self.config["servicio_min"]
        maximo = self.config["servicio_max"]
        return random.randint(minimo, maximo) if minimo != maximo else minimo

    def generar_tiempo_salida_servidor(self):
        minimo = self.config["salida_min"]
        maximo = self.config["salida_max"]
        return random.randint(minimo, maximo) if minimo != maximo else minimo

    def generar_tiempo_llegada_servidor(self):
        minimo = self.config["descanso_min"]
        maximo = self.config["descanso_max"]
        return random.randint(minimo, maximo) if minimo != maximo else minimo

    def generar_tiempo_abandono_a(self):
        minimo = self.config["abandono_a_min"]
        maximo = self.config["abandono_a_max"]
        return random.randint(minimo, maximo) if minimo != maximo else minimo

    def generar_tiempo_abandono_b(self):
        minimo = self.config["abandono_b_min"]
        maximo = self.config["abandono_b_max"]
        return random.randint(minimo, maximo) if minimo != maximo else minimo

    #  Métodos de obtención de próximos eventos 

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
        #Intentamos buscar un evento de fin de servicio que sea válido (servidor presente)
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.FIN_SERVICIO and evento[2].valido:
                return evento[0]

        # Si no hay evento válido, pero el servidor está ausente y el PS ocupado. Entonces proyectamos el fin de servicio para la tabla, para que el usuario tenga una referencia de cuándo podría terminar el servicio del cliente actual si el servidor regresa pronto. (Es sólo estético, no afecta la lógica de la simulación)
        if not self.sistema.servidor and self.sistema.puesto_de_servicio:
            hora_regreso_sv = self.obtener_proximo_trabajo()
            tiempo_restante = self.sistema.tiempo_restante_servicio_actual

            # Si tenemos ambos datos, proyectamos el fin de servicio para la tabla
            if hora_regreso_sv != "" and tiempo_restante is not None:
                return hora_regreso_sv + tiempo_restante

        return ""  # Realmente vacío solo si no hay nadie en el PS

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

    def obtener_proximo_abandono(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.ABANDONO and evento[2].valido:
                return evento[0]  # Retorna el tiempo del próximo abandono
        return ""  # Si no hay eventos de abandono programados

    def obtener_proximo_abandono_a(self):
        ids_cola_a = [cliente.id for cliente in self.sistema.cola_A]
        for evento in self.eventos:
            if (evento[2].tipo == TipoEvento.ABANDONO and evento[2].valido and evento[2].id_cliente in ids_cola_a): #
                return evento[0]  # Retorna el tiempo del próximo abandono de un cliente tipo A
        return ""  # Si no hay eventos de abandono de clientes tipo A programados

    def obtener_proximo_abandono_b(self):
        ids_cola_b = [cliente.id for cliente in self.sistema.cola_B]
        for evento in self.eventos:
            if (evento[2].tipo == TipoEvento.ABANDONO and evento[2].valido and evento[2].id_cliente in ids_cola_b ):
                return evento[0]  # Retorna el tiempo del próximo abandono de un cliente tipo B
        return ""  # Si no hay eventos de abandono de clientes tipo B programados

    #  Procesadores de eventos 

    def procesar_llegada(self, evento):
        tiene_abandono = self.config["tiene_abandono"]

        if (
            not self.sistema.puesto_de_servicio and self.sistema.servidor
        ):  # Si el puesto de servicio está desocupado y el servidor está disponible
            self.sistema.puesto_de_servicio = True  # Ocupamos el puesto de servicio
            tiempo_servicio = (
                self.generar_tiempo_servicio()
            )  # Generar el tiempo de servicio
            evento_fin = Evento(
                TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio
            )  # Crear el evento de fin de servicio
            self.sistema.tiempo_fin_servicio_actual = (
                self.tiempo_actual + tiempo_servicio
            )
            heapq.heappush(
                self.eventos,
                (
                    self.tiempo_actual + tiempo_servicio,
                    self.contador_eventos,
                    evento_fin,
                ),
            )
            self.contador_eventos += 1
            self._tiempo_inicio_servicio = self.tiempo_actual
            self.tiempos_espera.append(0)  # El cliente no esperó en cola
        else:
            nuevo_cliente = Cliente(
                self.contador_clientes, self.tiempo_actual, "general"
            )
            self.sistema.cola.append(nuevo_cliente)  # Agregar el cliente a la cola
            self.contador_clientes += 1

            # Generar el próximo evento de abandono para el cliente que acaba de llegar (si aplica)
            if tiene_abandono:
                tiempo_abandono = (
                    self.generar_tiempo_abandono_a()
                )  # Se usa abandono_a para clientes generales
                evento_abandono = Evento(
                    TipoEvento.ABANDONO, self.tiempo_actual + tiempo_abandono
                )
                evento_abandono.id_cliente = nuevo_cliente.id
                heapq.heappush(
                    self.eventos,
                    (
                        self.tiempo_actual + tiempo_abandono,
                        self.contador_eventos,
                        evento_abandono,
                    ),
                )
                self.contador_eventos += 1

        # Generar el próximo evento de llegada
        tiempo_llegada = self.generar_tiempo_llegada()
        evento_llegada = Evento(TipoEvento.LLEGADA, self.tiempo_actual + tiempo_llegada)
        heapq.heappush(
            self.eventos,
            (
                self.tiempo_actual + tiempo_llegada,
                self.contador_eventos,
                evento_llegada,
            ),
        )
        self.contador_eventos += 1

    def procesar_llegada_a(self, evento):
        tiene_abandono = self.config["tiene_abandono"]

        if (
            not self.sistema.puesto_de_servicio and self.sistema.servidor
        ):  # Si el puesto de servicio está desocupado y el servidor está disponible
            self.sistema.puesto_de_servicio = True  # Ocupamos el puesto de servicio
            tiempo_servicio = (
                self.generar_tiempo_servicio()
            )  # Generar el tiempo de servicio
            evento_fin = Evento(
                TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio
            )  # Crear el evento de fin de servicio
            self.sistema.tiempo_fin_servicio_actual = (
                self.tiempo_actual + tiempo_servicio
            )
            heapq.heappush(
                self.eventos,
                (
                    self.tiempo_actual + tiempo_servicio,
                    self.contador_eventos,
                    evento_fin,
                ),
            )
            self.contador_eventos += 1
            self._tiempo_inicio_servicio = self.tiempo_actual
            self.tiempos_espera.append(0)  # El cliente no esperó en cola
            self.tiempos_espera_a.append(0)
        else:
            nuevo_cliente = Cliente(self.contador_clientes, self.tiempo_actual, "A")
            self.sistema.cola_A.append(
                nuevo_cliente
            )  # Agregar el cliente tipo A a la cola de tipo A
            self.contador_clientes += 1

            # Generar el próximo evento de abandono para el cliente tipo A que acaba de llegar (si aplica)
            if tiene_abandono:
                tiempo_abandono = (
                    self.generar_tiempo_abandono_a()
                )  # Generar el tiempo hasta el abandono del cliente tipo A
                evento_abandono = Evento(
                    TipoEvento.ABANDONO, self.tiempo_actual + tiempo_abandono
                )
                evento_abandono.id_cliente = nuevo_cliente.id
                heapq.heappush(
                    self.eventos,
                    (
                        self.tiempo_actual + tiempo_abandono,
                        self.contador_eventos,
                        evento_abandono,
                    ),
                )
                self.contador_eventos += 1

        # Generar el próximo evento de llegada para clientes tipo A
        tiempo_llegada_a = self.generar_tiempo_llegada_a()
        evento_llegada_a = Evento(
            TipoEvento.LLEGADA_A, self.tiempo_actual + tiempo_llegada_a
        )
        heapq.heappush(
            self.eventos,
            (
                self.tiempo_actual + tiempo_llegada_a,
                self.contador_eventos,
                evento_llegada_a,
            ),
        )
        self.contador_eventos += 1

    def procesar_llegada_b(self, evento):
        tiene_abandono = self.config["tiene_abandono"]

        if (
            not self.sistema.puesto_de_servicio and self.sistema.servidor
        ):  # Si el puesto de servicio está desocupado y el servidor está disponible
            self.sistema.puesto_de_servicio = True  # Ocupamos el puesto de servicio
            tiempo_servicio = (
                self.generar_tiempo_servicio()
            )  # Generar el tiempo de servicio
            evento_fin = Evento(
                TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio
            )  # Crear el evento de fin de servicio
            self.sistema.tiempo_fin_servicio_actual = (
                self.tiempo_actual + tiempo_servicio
            )
            heapq.heappush(
                self.eventos,
                (
                    self.tiempo_actual + tiempo_servicio,
                    self.contador_eventos,
                    evento_fin,
                ),
            )
            self.contador_eventos += 1
            self._tiempo_inicio_servicio = self.tiempo_actual
            self.tiempos_espera.append(0)  # El cliente no esperó en cola
            self.tiempos_espera_b.append(0)
        else:
            nuevo_cliente = Cliente(self.contador_clientes, self.tiempo_actual, "B")
            self.sistema.cola_B.append(
                nuevo_cliente
            )  # Agregar el cliente tipo B a la cola de tipo B
            self.contador_clientes += 1

            # Generar el próximo evento de abandono para el cliente tipo B que acaba de llegar (si aplica)
            if tiene_abandono:
                tiempo_abandono = (
                    self.generar_tiempo_abandono_b()
                )  # Generar el tiempo hasta el abandono del cliente tipo B
                evento_abandono = Evento(
                    TipoEvento.ABANDONO, self.tiempo_actual + tiempo_abandono
                )
                evento_abandono.id_cliente = nuevo_cliente.id
                heapq.heappush(
                    self.eventos,
                    (
                        self.tiempo_actual + tiempo_abandono,
                        self.contador_eventos,
                        evento_abandono,
                    ),
                )
                self.contador_eventos += 1

        # Generar el próximo evento de llegada para clientes tipo B
        tiempo_llegada_b = self.generar_tiempo_llegada_b()
        evento_llegada_b = Evento(
            TipoEvento.LLEGADA_B, self.tiempo_actual + tiempo_llegada_b
        )
        heapq.heappush(
            self.eventos,
            (
                self.tiempo_actual + tiempo_llegada_b,
                self.contador_eventos,
                evento_llegada_b,
            ),
        )
        self.contador_eventos += 1

    def procesar_fin_servicio(self, evento):
        tiene_prioridad = self.config["tiene_prioridad"]
        tiene_abandono = self.config["tiene_abandono"]

        # Registrar tiempo de ocupación del PS para el cliente que termina
        if self._tiempo_inicio_servicio is not None:
            self.tiempo_servidor_ocupado += (
                self.tiempo_actual - self._tiempo_inicio_servicio
            )
            self._tiempo_inicio_servicio = None

        # Determinar si hay clientes en cola
        if tiene_prioridad:
            hay_cola = bool(self.sistema.cola_A or self.sistema.cola_B)
        else:
            hay_cola = bool(self.sistema.cola)

        if hay_cola:
            # Sacar al próximo cliente según prioridad
            if tiene_prioridad:
                if self.sistema.cola_A:
                    cliente_atendido = self.sistema.cola_A.pop(
                        0
                    )  # Sacar al primer cliente de tipo A de la cola
                    cola_salida = "A"
                else:
                    cliente_atendido = self.sistema.cola_B.pop(
                        0
                    )  # Sacar al primer cliente de tipo B de la cola
                    cola_salida = "B"
            else:
                cliente_atendido = self.sistema.cola.pop(
                    0
                )  # Sacar al primer cliente de la cola
                cola_salida = "general"

            # Registrar métricas del cliente que termina de ser atendido
            self.clientes_atendidos += 1
            if cola_salida == "A":
                self.clientes_atendidos_a += 1
            elif cola_salida == "B":
                self.clientes_atendidos_b += 1

            # Registrar tiempo de espera del cliente que sale de la cola hacia el PS
            tiempo_espera = self.tiempo_actual - cliente_atendido.hora_llegada
            self.tiempos_espera.append(tiempo_espera)
            if cola_salida == "A":
                self.tiempos_espera_a.append(tiempo_espera)
            elif cola_salida == "B":
                self.tiempos_espera_b.append(tiempo_espera)

            # Iniciar servicio para el siguiente cliente
            tiempo_servicio = (
                self.generar_tiempo_servicio()
            )  # Generar el tiempo de servicio para el siguiente cliente
            evento_fin = Evento(
                TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio
            )  # Crear el evento de fin de servicio para el siguiente cliente
            self.sistema.tiempo_fin_servicio_actual = (
                self.tiempo_actual + tiempo_servicio
            )
            heapq.heappush(
                self.eventos,
                (
                    self.tiempo_actual + tiempo_servicio,
                    self.contador_eventos,
                    evento_fin,
                ),
            )
            self.contador_eventos += 1
            self._tiempo_inicio_servicio = self.tiempo_actual

            # Invalidar el evento de abandono del cliente que acaba de pasar al PS (si aplica)
            if tiene_abandono:
                for i in range(len(self.eventos)):
                    if (
                        self.eventos[i][2].tipo == TipoEvento.ABANDONO
                        and self.eventos[i][2].id_cliente == cliente_atendido.id
                    ):
                        self.eventos[i][
                            2
                        ].valido = False  # Marcar el evento de abandono como inválido
                        break

        else:
            # Registrar al último cliente atendido antes de que el PS quede libre
            self.clientes_atendidos += 1
            self.sistema.puesto_de_servicio = False  # Si no hay clientes en la cola, el puesto de servicio queda desocupado
            self.sistema.tiempo_fin_servicio_actual = (
                None  # Reiniciar el tiempo de fin de servicio actual
            )

    def procesar_salida_servidor(self, evento):
        self.sistema.servidor = (
            False  # El servidor sale, por lo que se marca como no disponible
        )
        self._tiempo_inicio_ausencia = (
            self.tiempo_actual
        )  # Registrar inicio de ausencia

        # Si el servidor sale mientras un cliente está siendo atendido, se invalida el evento de fin de servicio actual
        if self.sistema.tiempo_fin_servicio_actual is not None:
            for i in range(len(self.eventos)):
                if (
                    self.eventos[i][2].tipo == TipoEvento.FIN_SERVICIO
                    and self.eventos[i][0] == self.sistema.tiempo_fin_servicio_actual
                ):
                    self.eventos[i][
                        2
                    ].valido = (
                        False  # Marcar el evento de fin de servicio como inválido
                    )
                    break
            # Calcular el tiempo restante de servicio para el cliente actual
            self.sistema.tiempo_restante_servicio_actual = (
                self.sistema.tiempo_fin_servicio_actual - self.tiempo_actual
            )

        # Generar el próximo evento de llegada del servidor
        tiempo_llegada_servidor = (
            self.generar_tiempo_llegada_servidor()
        )  # Generar el tiempo hasta la próxima llegada del servidor
        evento_llegada_servidor = Evento(
            TipoEvento.LLEGADA_SERVIDOR, self.tiempo_actual + tiempo_llegada_servidor
        )
        heapq.heappush(
            self.eventos,
            (
                self.tiempo_actual + tiempo_llegada_servidor,
                self.contador_eventos,
                evento_llegada_servidor,
            ),
        )
        self.contador_eventos += 1

    def procesar_llegada_servidor(self, evento):
        tiene_prioridad = self.config["tiene_prioridad"]
        tiene_abandono = self.config["tiene_abandono"]

        self.sistema.servidor = (
            True  # El servidor llega, por lo que se marca como disponible
        )

        # Registrar tiempo de ausencia
        if self._tiempo_inicio_ausencia is not None:
            self.tiempo_servidor_ausente += (
                self.tiempo_actual - self._tiempo_inicio_ausencia
            )
            self._tiempo_inicio_ausencia = None

        # Si el servidor llega y hay un cliente esperando en el puesto de servicio, se reanuda su servicio
        if (
            self.sistema.puesto_de_servicio
            and self.sistema.tiempo_restante_servicio_actual is not None
        ):
            tiempo_fin_servicio = (
                self.tiempo_actual + self.sistema.tiempo_restante_servicio_actual
            )  # Calcular el nuevo tiempo de fin de servicio para el cliente actual
            evento_fin = Evento(TipoEvento.FIN_SERVICIO, tiempo_fin_servicio)
            self.sistema.tiempo_fin_servicio_actual = tiempo_fin_servicio
            heapq.heappush(
                self.eventos, (tiempo_fin_servicio, self.contador_eventos, evento_fin)
            )
            self.contador_eventos += 1
            self.sistema.tiempo_restante_servicio_actual = None
            self._tiempo_inicio_servicio = (
                self.tiempo_actual
            )  # Reanudamos el conteo de ocupación

        # Si el servidor llega y el puesto está libre pero hay clientes en cola, se atiende al siguiente
        elif not self.sistema.puesto_de_servicio:
            if tiene_prioridad:
                hay_cola = bool(self.sistema.cola_A or self.sistema.cola_B)
            else:
                hay_cola = bool(self.sistema.cola)

            if hay_cola:
                self.sistema.puesto_de_servicio = True

                if tiene_prioridad:
                    if self.sistema.cola_A:
                        cliente_atendido = self.sistema.cola_A.pop(
                            0
                        )  # Sacar al primer cliente de tipo A de la cola
                        cola_salida = "A"
                    else:
                        cliente_atendido = self.sistema.cola_B.pop(
                            0
                        )  # Sacar al primer cliente de tipo B de la cola
                        cola_salida = "B"
                else:
                    cliente_atendido = self.sistema.cola.pop(
                        0
                    )  # Sacar al primer cliente de la cola
                    cola_salida = "general"

                # Registrar tiempo de espera
                tiempo_espera = self.tiempo_actual - cliente_atendido.hora_llegada
                self.tiempos_espera.append(tiempo_espera)
                if cola_salida == "A":
                    self.tiempos_espera_a.append(tiempo_espera)
                elif cola_salida == "B":
                    self.tiempos_espera_b.append(tiempo_espera)

                tiempo_servicio = (
                    self.generar_tiempo_servicio()
                )  # Generar el tiempo de servicio para el siguiente cliente
                evento_fin = Evento(
                    TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio
                )
                self.sistema.tiempo_fin_servicio_actual = (
                    self.tiempo_actual + tiempo_servicio
                )
                heapq.heappush(
                    self.eventos,
                    (
                        self.tiempo_actual + tiempo_servicio,
                        self.contador_eventos,
                        evento_fin,
                    ),
                )
                self.contador_eventos += 1
                self.sistema.tiempo_restante_servicio_actual = None
                self._tiempo_inicio_servicio = self.tiempo_actual

                # Invalidar abandono del cliente que pasa al PS (si aplica)
                if tiene_abandono:
                    for i in range(len(self.eventos)):
                        if (
                            self.eventos[i][2].tipo == TipoEvento.ABANDONO
                            and self.eventos[i][2].id_cliente == cliente_atendido.id
                        ):
                            self.eventos[i][
                                2
                            ].valido = (
                                False  # Marcar el evento de abandono como inválido
                            )
                            break

        # Generar el próximo evento de salida del servidor
        tiempo_salida_servidor = (
            self.generar_tiempo_salida_servidor()
        )  # Generar el tiempo hasta la próxima salida del servidor
        evento_salida_servidor = Evento(
            TipoEvento.SALIDA_SERVIDOR, self.tiempo_actual + tiempo_salida_servidor
        )
        heapq.heappush(
            self.eventos,
            (
                self.tiempo_actual + tiempo_salida_servidor,
                self.contador_eventos,
                evento_salida_servidor,
            ),
        )
        self.contador_eventos += 1

    def procesar_abandono(self, evento):
        tiene_prioridad = self.config["tiene_prioridad"]

        if tiene_prioridad:
            # Buscar el cliente por ID en cola A o B
            if self.sistema.cola_A and evento.id_cliente in [
                cliente.id for cliente in self.sistema.cola_A
            ]:
                cliente_abandono = next(
                    cliente
                    for cliente in self.sistema.cola_A
                    if cliente.id == evento.id_cliente
                )
                self.sistema.cola_A.remove(
                    cliente_abandono
                )  # Eliminar al cliente de tipo A que abandona
                self.clientes_abandonaron += 1
                self.clientes_abandonaron_a += 1

            elif self.sistema.cola_B and evento.id_cliente in [
                cliente.id for cliente in self.sistema.cola_B
            ]:
                cliente_abandono = next(
                    cliente
                    for cliente in self.sistema.cola_B
                    if cliente.id == evento.id_cliente
                )
                self.sistema.cola_B.remove(
                    cliente_abandono
                )  # Eliminar al cliente de tipo B que abandona
                self.clientes_abandonaron += 1
                self.clientes_abandonaron_b += 1
        else:
            # Buscar el cliente por ID en la cola general
            if self.sistema.cola and evento.id_cliente in [
                cliente.id for cliente in self.sistema.cola
            ]:
                cliente_abandono = next(
                    cliente
                    for cliente in self.sistema.cola
                    if cliente.id == evento.id_cliente
                )
                self.sistema.cola.remove(
                    cliente_abandono
                )  # Eliminar al cliente que abandona
                self.clientes_abandonaron += 1

    def obtener_metricas(self):
        """Devuelve un diccionario con todas las métricas al final de la simulación."""
        tiene_prioridad = self.config["tiene_prioridad"]
        tiene_descanso = self.config["tiene_descanso"]

        def promedio(lista):
            return round(sum(lista) / len(lista), 2) if lista else 0

        def maximo(lista):
            return max(lista) if lista else 0

        ocupacion = (
            round((self.tiempo_servidor_ocupado / self.tiempo_total) * 100, 1)
            if self.tiempo_total > 0
            else 0
        )

        metricas = {
            "clientes_atendidos": self.clientes_atendidos,
            "clientes_abandonaron": self.clientes_abandonaron,
            "espera_promedio": promedio(self.tiempos_espera),
            "espera_maxima": maximo(self.tiempos_espera),
            "ocupacion_servidor": ocupacion,
            "tiempo_servidor_ocupado": round(self.tiempo_servidor_ocupado, 2),
        }

        if tiene_descanso:
            metricas["tiempo_servidor_ausente"] = round(self.tiempo_servidor_ausente, 2)

        if tiene_prioridad:
            metricas["clientes_atendidos_a"] = self.clientes_atendidos_a
            metricas["clientes_atendidos_b"] = self.clientes_atendidos_b
            metricas["clientes_abandonaron_a"] = self.clientes_abandonaron_a
            metricas["clientes_abandonaron_b"] = self.clientes_abandonaron_b
            metricas["espera_promedio_a"] = promedio(self.tiempos_espera_a)
            metricas["espera_promedio_b"] = promedio(self.tiempos_espera_b)
            metricas["espera_maxima_a"] = maximo(self.tiempos_espera_a)
            metricas["espera_maxima_b"] = maximo(self.tiempos_espera_b)

        return metricas

    #  Inicio y encabezado 

    def inicio(self):
        tiene_prioridad = self.config["tiene_prioridad"]
        tiene_descanso = self.config["tiene_descanso"]

        # Generar el primer evento de llegada según configuración
        if tiene_prioridad:
            tiempo_a = (
                self.generar_tiempo_llegada_a()
            )  # Generar el tiempo de llegada del primer cliente tipo A
            evento_a = Evento(TipoEvento.LLEGADA_A, tiempo_a)
            heapq.heappush(self.eventos, (tiempo_a, self.contador_eventos, evento_a))
            self.contador_eventos += 1

            tiempo_b = (
                self.generar_tiempo_llegada_b()
            )  # Generar el tiempo de llegada del primer cliente tipo B
            evento_b = Evento(TipoEvento.LLEGADA_B, tiempo_b)
            heapq.heappush(self.eventos, (tiempo_b, self.contador_eventos, evento_b))
            self.contador_eventos += 1
        else:
            tiempo = (
                self.generar_tiempo_llegada()
            )  # Generar el tiempo de llegada del primer cliente
            evento = Evento(TipoEvento.LLEGADA, tiempo)
            heapq.heappush(self.eventos, (tiempo, self.contador_eventos, evento))
            self.contador_eventos += 1

        # Generar el primer evento de salida del servidor (si el servidor puede descansar)
        if tiene_descanso:
            tiempo_salida_servidor = self.generar_tiempo_salida_servidor()
            evento_salida_servidor = Evento(
                TipoEvento.SALIDA_SERVIDOR, tiempo_salida_servidor
            )
            heapq.heappush(
                self.eventos,
                (tiempo_salida_servidor, self.contador_eventos, evento_salida_servidor),
            )
            self.contador_eventos += 1

        # Imprimir encabezados de la tabla según configuración
        self._imprimir_encabezado()

    def _imprimir_encabezado(self):
        tiene_prioridad = self.config["tiene_prioridad"]
        tiene_descanso = self.config["tiene_descanso"]
        tiene_abandono = self.config["tiene_abandono"]

        cols = [f"{'Hora actual':^15}"]
        sep = ["-" * 15]

        if tiene_prioridad:
            cols += [f"{'Próx. llegada A':^17}", f"{'Próx. llegada B':^17}"]
            sep += ["-" * 17, "-" * 17]
        else:
            cols += [f"{'Próx. llegada':^17}"]
            sep += ["-" * 17]

        cols += [f"{'Próx. fin serv.':^20}"]
        sep += ["-" * 20]

        if tiene_descanso:
            cols += [f"{'Hora Descanso':^15}", f"{'Hora Trabajo':^15}"]
            sep += ["-" * 15, "-" * 15]

        if tiene_abandono:
            if tiene_prioridad:
                cols += [f"{'Hora abandono A':^17}", f"{'Hora abandono B':^17}"]
                sep += ["-" * 17, "-" * 17]
            else:
                cols += [f"{'Hora de abandono':^17}"]
                sep += ["-" * 17]

        cols += [f"{'PS':^7}"]
        sep += ["-" * 7]

        if tiene_prioridad:
            cols += [f"{'Cola A':^7}", f"{'Cola B':^7}"]
            sep += ["-" * 7, "-" * 7]
        else:
            cols += [f"{'Cola':^7}"]
            sep += ["-" * 7]

        if tiene_descanso:
            cols += [f"{'Servidor':^10}"]
            sep += ["-" * 10]

        cols += [f"{'Gráficamente':^15}"]
        sep += ["-" * 15]

        print("|" + "|".join(cols) + "|")
        print("|" + "|".join(sep) + "|")

    #  Ejecutar 

    def ejecutar(self):
        tiene_prioridad = self.config["tiene_prioridad"]
        tiene_descanso = self.config["tiene_descanso"]
        tiene_abandono = self.config["tiene_abandono"]

        while self.eventos: # Mientras haya eventos programados en la simulación
            evento = heapq.heappop(self.eventos)
            if not evento[2].valido:  # Si el evento ha sido invalidado, se ignora y se continúa con el siguiente evento
                continue

            if evento[0] > self.tiempo_total:
                break  # Si el tiempo del evento excede el tiempo total de simulación, se detiene la simulación

            self.tiempo_actual = evento[0]  # Actualizar el tiempo actual al tiempo del evento

            if evento[2].tipo == TipoEvento.LLEGADA:
                self.procesar_llegada(evento[2])  # Procesar el evento de llegada
            elif evento[2].tipo == TipoEvento.LLEGADA_A:
                self.procesar_llegada_a(
                    evento[2]
                )  # Procesar el evento de llegada de un cliente tipo A
            elif evento[2].tipo == TipoEvento.LLEGADA_B:
                self.procesar_llegada_b(
                    evento[2]
                )  # Procesar el evento de llegada de un cliente tipo B
            elif evento[2].tipo == TipoEvento.FIN_SERVICIO:
                self.procesar_fin_servicio(
                    evento[2]
                )  # Procesar el evento de fin de servicio
            elif evento[2].tipo == TipoEvento.SALIDA_SERVIDOR:
                self.procesar_salida_servidor(
                    evento[2]
                )  # Procesar el evento de salida del servidor
            elif evento[2].tipo == TipoEvento.LLEGADA_SERVIDOR:
                self.procesar_llegada_servidor(
                    evento[2]
                )  # Procesar el evento de llegada del servidor
            elif evento[2].tipo == TipoEvento.ABANDONO:
                self.procesar_abandono(evento[2])  # Procesar el evento de abandono

            # Imprimir el estado actual del sistema después de procesar el evento
            self._imprimir_fila()

    def _imprimir_fila(self):
        tiene_prioridad = self.config["tiene_prioridad"]
        tiene_descanso = self.config["tiene_descanso"]
        tiene_abandono = self.config["tiene_abandono"]

        vals = [f"{self.tiempo_actual:^15}"]

        if tiene_prioridad:
            vals += [
                f"{self.obtener_proxima_llegada_a():^17}",
                f"{self.obtener_proxima_llegada_b():^17}",
            ]
        else:
            vals += [f"{self.obtener_proxima_llegada():^17}"]

        vals += [f"{self.obtener_proximo_fin_servicio():^20}"]

        if tiene_descanso:
            vals += [
                f"{self.obtener_proximo_descanso():^15}",
                f"{self.obtener_proximo_trabajo():^15}",
            ]

        if tiene_abandono:
            if tiene_prioridad:
                vals += [
                    f"{self.obtener_proximo_abandono_a():^17}",
                    f"{self.obtener_proximo_abandono_b():^17}",
                ]
            else:
                vals += [f"{self.obtener_proximo_abandono():^17}"]

        vals += [f"{self.sistema.puesto_de_servicio:^7}"]

        if tiene_prioridad:
            vals += [f"{len(self.sistema.cola_A):^7}", f"{len(self.sistema.cola_B):^7}"]
        else:
            vals += [f"{len(self.sistema.cola):^7}"]

        if tiene_descanso:
            vals += [f"{self.sistema.servidor:^10}"]

        # Representación gráfica del estado del sistema
        grafico = "⧇" if self.sistema.puesto_de_servicio else "▢"
        if tiene_descanso:
            grafico += "D" if self.sistema.servidor else " "
        else:
            grafico += "D"
        if tiene_prioridad:
            grafico += "A" * len(self.sistema.cola_A) + "B" * len(self.sistema.cola_B)
        else:
            grafico += "O" * len(self.sistema.cola)

        vals += [f"{grafico:^15}"]

        print("|" + "|".join(vals) + "|")
