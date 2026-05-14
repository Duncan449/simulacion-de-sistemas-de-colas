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
        self.cliente_actual = None  # Variable para almacenar el cliente que está siendo atendido actualmente (si hay alguno)
        self.cantidad_descansos = 0  # Contador de la cantidad de veces que el servidor descansó
        self.clientes_atendidos_hasta_segundo_descanso = 0  # Contador de clientes atendidos hasta el segundo descanso del servidor 
        self.modo_carpintero = False  # Modo especial para generar tiempos de servicio más largos y variados, útil para probar la lógica de descanso del servidor

        # Aplicar vector inicial
        self._aplicar_vector_inicial()

    def _aplicar_vector_inicial(self):
        # Puebla el estado inicial del sistema según la configuración del vector inicial.
        vi = self.config.get("vector_inicial", {})
        if not vi:
            return # Si no hay vector inicial, no hacemos nada y el sistema arranca vacío y con el servidor presente.

        tiene_prioridad = self.config["tiene_prioridad"]
        tiene_descanso = self.config["tiene_descanso"]
        tiene_zona = self.config["tiene_zona_seguridad"]
        tiene_abandono = self.config["tiene_abandono"]

        # ── Estado del servidor inicial
        if tiene_descanso:
            servidor_presente = vi.get("servidor_presente", True) 
            self.sistema.servidor = servidor_presente
            if not servidor_presente:
                tiempo_regreso = vi.get("tiempo_regreso_servidor", 0) or 0 
                if tiempo_regreso > 0:
                    evento_regreso = Evento(TipoEvento.LLEGADA_SERVIDOR, tiempo_regreso)
                    heapq.heappush(
                        self.eventos,
                        (tiempo_regreso, self.contador_eventos, evento_regreso),
                    )
                    self.contador_eventos += 1
                self._tiempo_inicio_ausencia = 0  # Empezó ausente desde t=0

        # ── Cola inicial
        # Los clientes se agregan a la cola con hora_llegada negativa para que
        # su tiempo de espera impacte correctamente en el promedio.
        # Si abandono está activo, se programa el evento de abandono de cada uno
        # considerando que llevan 'espera' segundos esperando, por lo que su
        # tiempo restante de paciencia es (paciencia_total - espera_ya_transcurrida).
        if tiene_prioridad:
            cantidad_a = vi.get("cola_a_cantidad", 0) or 0
            tiempos_a = vi.get("cola_a_tiempos", []) or []
            for i in range(cantidad_a):
                espera = tiempos_a[i] if i < len(tiempos_a) else 0
                hora_llegada = -espera
                cliente = Cliente(self.contador_clientes, hora_llegada, "A")
                self.sistema.cola_A.append(cliente)
                self.contador_clientes += 1
                if tiene_abandono:
                    paciencia_total = self.generar_tiempo_abandono_a()
                    tiempo_restante_paciencia = max(1, paciencia_total - espera)
                    evento_abandono = Evento(
                        TipoEvento.ABANDONO, tiempo_restante_paciencia
                    )
                    evento_abandono.id_cliente = cliente.id
                    heapq.heappush(
                        self.eventos,
                        (
                            tiempo_restante_paciencia,
                            self.contador_eventos,
                            evento_abandono,
                        ),
                    )
                    self.contador_eventos += 1

            cantidad_b = vi.get("cola_b_cantidad", 0) or 0
            tiempos_b = vi.get("cola_b_tiempos", []) or []
            for i in range(cantidad_b):
                espera = tiempos_b[i] if i < len(tiempos_b) else 0
                hora_llegada = -espera
                cliente = Cliente(self.contador_clientes, hora_llegada, "B")
                self.sistema.cola_B.append(cliente)
                self.contador_clientes += 1
                if tiene_abandono:
                    paciencia_total = self.generar_tiempo_abandono_b()
                    tiempo_restante_paciencia = max(1, paciencia_total - espera)
                    evento_abandono = Evento(
                        TipoEvento.ABANDONO, tiempo_restante_paciencia
                    )
                    evento_abandono.id_cliente = cliente.id
                    heapq.heappush(
                        self.eventos,
                        (
                            tiempo_restante_paciencia,
                            self.contador_eventos,
                            evento_abandono,
                        ),
                    )
                    self.contador_eventos += 1
        else:
            cantidad = vi.get("cola_cantidad", 0) or 0
            tiempos = vi.get("cola_tiempos", []) or []
            for i in range(cantidad):
                espera = tiempos[i] if i < len(tiempos) else 0
                hora_llegada = -espera
                cliente = Cliente(self.contador_clientes, hora_llegada, "general")
                self.sistema.cola.append(cliente)
                self.contador_clientes += 1
                if tiene_abandono:
                    paciencia_total = self.generar_tiempo_abandono_a()
                    tiempo_restante_paciencia = max(1, paciencia_total - espera)
                    evento_abandono = Evento(
                        TipoEvento.ABANDONO, tiempo_restante_paciencia
                    )
                    evento_abandono.id_cliente = cliente.id
                    heapq.heappush(
                        self.eventos,
                        (
                            tiempo_restante_paciencia,
                            self.contador_eventos,
                            evento_abandono,
                        ),
                    )
                    self.contador_eventos += 1
        # ── Zona de seguridad inicial
        if tiene_zona:
            zona_ocupada = vi.get("zona_ocupada", False) 
            if zona_ocupada:
                self.sistema.zona_seguridad_ocupada = True
                tiempo_llegada_ps = vi.get("tiempo_llegada_ps", 0) or 0
                if tiempo_llegada_ps > 0:
                    # Creamos un cliente "fantasma" para la zona de seguridad
                    cliente_zona = Cliente(self.contador_clientes, 0, "general")
                    self.contador_clientes += 1
                    self.cliente_actual = (
                        cliente_zona  # Este será el siguiente en el PS
                    )
                    evento_llegada_ps = Evento(
                        TipoEvento.LLEGADA_AL_PS, tiempo_llegada_ps
                    )
                    evento_llegada_ps.id_cliente = cliente_zona.id
                    heapq.heappush(
                        self.eventos,
                        (tiempo_llegada_ps, self.contador_eventos, evento_llegada_ps),
                    )
                    self.contador_eventos += 1

        # ── Estado del PS inicial
        ps_ocupado = vi.get("ps_ocupado", False)
        if ps_ocupado:
            self.sistema.puesto_de_servicio = True
            tiempo_restante = vi.get("ps_tiempo_restante", 0) or 0
            if tiempo_restante > 0:
                cliente_ps = Cliente(self.contador_clientes, 0, "general")
                self.contador_clientes += 1
                self.cliente_actual = cliente_ps
                self.sistema.tiempo_fin_servicio_actual = tiempo_restante
                evento_fin = Evento(TipoEvento.FIN_SERVICIO, tiempo_restante)
                heapq.heappush(
                    self.eventos, (tiempo_restante, self.contador_eventos, evento_fin)
                )
                self.contador_eventos += 1
                self._tiempo_inicio_servicio = 0  # Empezó a ser atendido en t=0

        # ── Si el PS arranca libre, servidor presente y hay cola: arrancar servicio ──
        # Esto evita que el primer evento de llegada "robe" el lugar del primero en cola
        elif (
            not self.sistema.puesto_de_servicio
            and self.sistema.servidor
            and self._cola_tiene_clientes()
        ):
            cliente_atendido, _ = self._sacar_siguiente_de_cola()
            self.cliente_actual = cliente_atendido
            tiempo_espera = (
                0 - cliente_atendido.hora_llegada
            )  # hora_llegada es negativa
            self.tiempos_espera.append(tiempo_espera)
            if tiene_abandono:
                self._invalidar_abandono(cliente_atendido.id)
            if tiene_zona:
                self._enviar_cliente_a_zona(cliente_atendido)
            else:
                self._iniciar_servicio_en_ps()
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

        if self.modo_carpintero:
            return random.randint(1800, 2400) + random.randint(600, 1200) + random.randint(5, 1800)

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
        # Obtenemos los valores de la config (o 0 si no existen)
        min_val = self.config.get("abandono_a_min", 0)
        max_val = self.config.get("abandono_a_max", 0)

        # Forzamos a que si son None sean 0
        min_val = min_val if min_val is not None else 0
        max_val = max_val if max_val is not None else 0

        # Retornamos el random (si min y max son 0, devuelve 0)
        return random.randint(min_val, max_val)

    def generar_tiempo_abandono_b(self):
        # Obtenemos los valores de la config (o 0 si no existen)
        min_val = self.config.get("abandono_b_min", 0)
        max_val = self.config.get("abandono_b_max", 0)

        # Forzamos a que si son None sean 0
        min_val = min_val if min_val is not None else 0
        max_val = max_val if max_val is not None else 0

        # Retornamos el random (si min y max son 0, devuelve 0)
        return random.randint(min_val, max_val)

    def generar_tiempo_caminata(self):
        minimo = self.config["caminata_min"]
        maximo = self.config["caminata_max"]
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
        # Intentamos buscar un evento de fin de servicio que sea válido (servidor presente)
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

    def obtener_proxima_llegada_al_ps(self):
        for evento in self.eventos:
            if evento[2].tipo == TipoEvento.LLEGADA_AL_PS and evento[2].valido:
                return evento[0]  # Retorna el tiempo de la próxima llegada al PS (cuando el servidor regresa y atiende al cliente que estaba en el PS al momento de su salida)
        return ""  # Si no hay eventos de llegada al PS programados

    # Auxiliares
    def _enviar_cliente_a_zona(self, cliente, tipo_cliente="general"):
        # Envía un cliente a la Zona de seguridad y programa su llegada al PS
        self.sistema.zona_seguridad_ocupada = True
        tiempo_caminata = self.generar_tiempo_caminata()
        evento_llegada_ps = Evento(
            TipoEvento.LLEGADA_AL_PS, self.tiempo_actual + tiempo_caminata
        )
        evento_llegada_ps.id_cliente = cliente.id
        heapq.heappush(
            self.eventos,
            (
                self.tiempo_actual + tiempo_caminata,
                self.contador_eventos,
                evento_llegada_ps,
            ),
        )
        self.contador_eventos += 1

    def _cola_tiene_clientes(self):
        # Retorna True si hay algún cliente en cualquiera de las colas activas.
        tiene_prioridad = self.config["tiene_prioridad"]
        if tiene_prioridad:
            return bool(self.sistema.cola_A or self.sistema.cola_B)
        return bool(self.sistema.cola)

    def _sacar_siguiente_de_cola(self):
        # Saca al próximo cliente de la cola según prioridad. Retorna (cliente, tipo).
        tiene_prioridad = self.config["tiene_prioridad"]
        if tiene_prioridad:
            if self.sistema.cola_A:
                return self.sistema.cola_A.pop(0), "A"
            else:
                return self.sistema.cola_B.pop(0), "B"
        return self.sistema.cola.pop(0), "general"

    def _programar_abandono(self, cliente, tiempo_abandono):
        # Programa un evento de abandono para un cliente en cola.
        evento_abandono = Evento(
            TipoEvento.ABANDONO, self.tiempo_actual + tiempo_abandono
        )
        evento_abandono.id_cliente = cliente.id
        heapq.heappush(
            self.eventos,
            (
                self.tiempo_actual + tiempo_abandono,
                self.contador_eventos,
                evento_abandono,
            ),
        )
        self.contador_eventos += 1

    def _invalidar_abandono(self, id_cliente):
        # Invalida el evento de abandono de un cliente que ya fue atendido.
        for i in range(len(self.eventos)):
            if (
                self.eventos[i][2].tipo == TipoEvento.ABANDONO
                and self.eventos[i][2].id_cliente == id_cliente
            ):
                self.eventos[i][2].valido = False
                break               
    # Procesadores de eventos

    def procesar_llegada_al_ps(self, evento):
        # El cliente termina de caminar por la zona de seguridad y llega al PS.
        self.sistema.zona_seguridad_ocupada = (
            False  # El cliente ya llegó al PS, la zona queda libre
        )
        self._iniciar_servicio_en_ps()

    def _iniciar_servicio_en_ps(self):
        # Programa el fin de servicio del cliente que acaba de llegar al PS.
        self.sistema.puesto_de_servicio = True
        tiempo_servicio = self.generar_tiempo_servicio()
        evento_fin = Evento(
            TipoEvento.FIN_SERVICIO, self.tiempo_actual + tiempo_servicio
        )
        self.sistema.tiempo_fin_servicio_actual = self.tiempo_actual + tiempo_servicio
        heapq.heappush(
            self.eventos,
            (self.tiempo_actual + tiempo_servicio, self.contador_eventos, evento_fin),
        )
        self.contador_eventos += 1
        self._tiempo_inicio_servicio = self.tiempo_actual

    def procesar_llegada(self, evento):
        tiene_zona = self.config["tiene_zona_seguridad"]
        tiene_abandono = self.config["tiene_abandono"]

        nuevo_cliente = Cliente(self.contador_clientes, self.tiempo_actual, "general")
        self.contador_clientes += 1

        if tiene_zona:
            # Con zona de seguridad: entrada directa solo si PS libre, zona libre y cola vacía

            if (
                not self.sistema.puesto_de_servicio
                and not self.sistema.zona_seguridad_ocupada
                and not self._cola_tiene_clientes()
            ):

                self.tiempos_espera.append(0)  # No esperó en cola
                self._enviar_cliente_a_zona(nuevo_cliente)
                self.cliente_actual = nuevo_cliente  # El cliente que va a zona de seguridad se considera el cliente actual, ya que es el siguiente en ser atendido una vez que llegue al PS
            else:
                self.sistema.cola.append(nuevo_cliente)
                if tiene_abandono:
                    self._programar_abandono(
                        nuevo_cliente, self.generar_tiempo_abandono_a()
                    )
        else:
            # sin zona de seguridad

            if (
                not self.sistema.puesto_de_servicio and self.sistema.servidor
            ):  # Si el puesto de servicio está desocupado y el servidor está disponible

                self._iniciar_servicio_en_ps()  # Programa el fin de servicio para el cliente que acaba de llegar al PS
                self.tiempos_espera.append(0)  # El cliente no esperó en cola
                self.cliente_actual = nuevo_cliente  # Actualizamos el cliente que está siendo atendido
            else:
                self.sistema.cola.append(nuevo_cliente)  # Agregar el cliente a la cola

                # Generar el próximo evento de abandono para el cliente que acaba de llegar (si aplica)
                if tiene_abandono:
                    self._programar_abandono(nuevo_cliente, self.generar_tiempo_abandono_a())

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
        tiene_zona = self.config["tiene_zona_seguridad"]
        tiene_abandono = self.config["tiene_abandono"]

        nuevo_cliente = Cliente(self.contador_clientes, self.tiempo_actual, "A")
        self.contador_clientes += 1

        if tiene_zona:
            if (
                not self.sistema.puesto_de_servicio
                and not self.sistema.zona_seguridad_ocupada
                and not self._cola_tiene_clientes()
            ):
                self.tiempos_espera.append(0) # El cliente no esperó en cola
                self.tiempos_espera_a.append(0) 
                self._enviar_cliente_a_zona(nuevo_cliente, "A")
                self.cliente_actual = nuevo_cliente  # El cliente que va a zona de seguridad se considera el cliente actual, ya que es el siguiente en ser atendido una vez que llegue al PS
            else:
                self.sistema.cola_A.append(nuevo_cliente)
                if tiene_abandono:
                    self._programar_abandono(
                        nuevo_cliente, self.generar_tiempo_abandono_a()
                    )
        else:        
            # Sin zona de seguridad
            if (not self.sistema.puesto_de_servicio and self.sistema.servidor):  # Si el puesto de servicio está desocupado y el servidor está disponible
                self._iniciar_servicio_en_ps()  # Programa el fin de servicio para el cliente que acaba de llegar al PS
                self.tiempos_espera.append(0)  # El cliente no esperó en cola
                self.tiempos_espera_a.append(0)
                self.cliente_actual = nuevo_cliente  # Actualizamos el cliente que está siendo atendido

            else:
                self.sistema.cola_A.append(nuevo_cliente)  # Agregar el cliente tipo A a la cola de tipo A

                # Generar el próximo evento de abandono para el cliente tipo A que acaba de llegar (si aplica)
                if tiene_abandono:
                    self._programar_abandono(
                        nuevo_cliente, self.generar_tiempo_abandono_a()
                    )

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
        tiene_zona = self.config["tiene_zona_seguridad"]
        tiene_abandono = self.config["tiene_abandono"]

        nuevo_cliente = Cliente(self.contador_clientes, self.tiempo_actual, "B")
        self.contador_clientes += 1

        if tiene_zona:
            if (
                not self.sistema.puesto_de_servicio
                and not self.sistema.zona_seguridad_ocupada
                and not self._cola_tiene_clientes()
            ):
                self.tiempos_espera.append(0) # El cliente no esperó en cola
                self.tiempos_espera_b.append(0) 
                self._enviar_cliente_a_zona(nuevo_cliente, "B")
                self.cliente_actual = nuevo_cliente  # El cliente que va a zona de seguridad se considera el cliente actual, ya que es el siguiente en ser atendido una vez que llegue al PS
            else:
                self.sistema.cola_B.append(nuevo_cliente)
                if tiene_abandono:
                    self._programar_abandono(
                        nuevo_cliente, self.generar_tiempo_abandono_b()
                    )
        else:        
            # Sin zona de seguridad
            if (not self.sistema.puesto_de_servicio and self.sistema.servidor):  # Si el puesto de servicio está desocupado y el servidor está disponible
                self._iniciar_servicio_en_ps()  # Programa el fin de servicio para el cliente que acaba de llegar al PS
                self.tiempos_espera.append(0)  # El cliente no esperó en cola
                self.tiempos_espera_b.append(0)
                self.cliente_actual = nuevo_cliente  # Actualizamos el cliente que está siendo atendido

            else:
                self.sistema.cola_B.append(nuevo_cliente)  # Agregar el cliente tipo B a la cola de tipo B

                # Generar el próximo evento de abandono para el cliente tipo B que acaba de llegar (si aplica)
                if tiene_abandono:
                    self._programar_abandono(
                        nuevo_cliente, self.generar_tiempo_abandono_b()
                    )

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
        tiene_abandono = self.config["tiene_abandono"]
        tiene_zona = self.config["tiene_zona_seguridad"]

        cliente_que_termina = self.cliente_actual # Tomamos el cliente que estaba siendo atendido

        # contamos el cliente que termina su servicio como atendido.
        self.clientes_atendidos += 1
        if cliente_que_termina.tipo == "A":
            self.clientes_atendidos_a += 1
        elif cliente_que_termina.tipo == "B":
            self.clientes_atendidos_b += 1

        # Contamos los clientes atendidos hasta el segundo descanso del servidor.
        if self.cantidad_descansos < 2:
            self.clientes_atendidos_hasta_segundo_descanso += 1

        # Registrar tiempo de ocupación del PS para el cliente que termina
        if self._tiempo_inicio_servicio is not None:
            self.tiempo_servidor_ocupado += (
                self.tiempo_actual - self._tiempo_inicio_servicio
            )
            self._tiempo_inicio_servicio = None

        # Determinar si hay clientes en cola
        hay_cola = self._cola_tiene_clientes()

        if hay_cola:
            # Sacar al próximo cliente según prioridad
            cliente_atendido, cola_salida = self._sacar_siguiente_de_cola()

            self.cliente_actual = cliente_atendido  # Actualizamos el cliente que está siendo atendido

            # Registrar tiempo de espera del cliente que sale de la cola hacia el PS
            tiempo_espera = self.tiempo_actual - cliente_atendido.hora_llegada
            self.tiempos_espera.append(tiempo_espera)
            if cola_salida == "A":
                self.tiempos_espera_a.append(tiempo_espera)
            elif cola_salida == "B":
                self.tiempos_espera_b.append(tiempo_espera)

            # Invalidar abandono del cliente que pasa a ser atendido
            if tiene_abandono:
                self._invalidar_abandono(cliente_atendido.id)

            if tiene_zona:
                # Con zona: el PS queda libre, el siguiente entra a la zona a caminar
                self.sistema.puesto_de_servicio = False
                self.sistema.tiempo_fin_servicio_actual = None
                self._enviar_cliente_a_zona(cliente_atendido, cola_salida)
            else:
                # Sin zona: el siguiente arranca servicio directamente
                self._iniciar_servicio_en_ps()

        else:
            self.sistema.puesto_de_servicio = False  # Si no hay clientes en la cola, el puesto de servicio queda desocupado
            self.sistema.tiempo_fin_servicio_actual = (
                None  # Reiniciar el tiempo de fin de servicio actual
            )
            self.cliente_actual = None  # Reiniciar el cliente que está siendo atendido

    def procesar_salida_servidor(self, evento):
        self.sistema.servidor = False  # El servidor sale, por lo que se marca como no disponible
        self._tiempo_inicio_ausencia = self.tiempo_actual # Registrar inicio de ausencia

        self.cantidad_descansos += 1  # Incrementar el contador de descansos del servidor

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
        tiene_abandono = self.config["tiene_abandono"]
        tiene_zona = self.config["tiene_zona_seguridad"]

        self.sistema.servidor = True  # El servidor llega, por lo que se marca como disponible

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
            # Reanudar servicio interrumpido
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
            self._tiempo_inicio_servicio = self.tiempo_actual # Reanudamos el conteo de ocupación

        # Si el servidor llega y el puesto está libre pero hay clientes en cola, se atiende al siguiente
        elif not self.sistema.puesto_de_servicio and self._cola_tiene_clientes():

            cliente_atendido, cola_salida = self._sacar_siguiente_de_cola() # Sacar al próximo cliente según prioridad

            self.cliente_actual = cliente_atendido  # Actualizamos el cliente que está siendo atendido

            tiempo_espera = self.tiempo_actual - cliente_atendido.hora_llegada
            self.tiempos_espera.append(tiempo_espera)
            if cola_salida == "A":
                self.tiempos_espera_a.append(tiempo_espera)
            elif cola_salida == "B":
                self.tiempos_espera_b.append(tiempo_espera)

            if tiene_abandono:
                self._invalidar_abandono(cliente_atendido.id)

            if tiene_zona:
                self._enviar_cliente_a_zona(cliente_atendido, cola_salida)
            else:
                self._iniciar_servicio_en_ps()

        # Generar el próximo evento de salida del servidor
        tiempo_salida_servidor = self.generar_tiempo_salida_servidor()
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
        # Devuelve un diccionario con todas las métricas al final de la simulación.
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
            "cantidad_descansos": self.cantidad_descansos,
            "clientes_atendidos_hasta_segundo_descanso": self.clientes_atendidos_hasta_segundo_descanso
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
        if tiene_descanso and self.sistema.servidor:  # Solo programamos la salida del servidor si el servidor está presente al inicio
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
        tiene_zona = self.config["tiene_zona_seguridad"]

        cols = [f"{'Hora actual':^15}"]
        sep = ["-" * 15]

        if tiene_prioridad:
            cols += [f"{'Próx. llegada A':^17}", f"{'Próx. llegada B':^17}"]
            sep += ["-" * 17, "-" * 17]
        else:
            cols += [f"{'Próx. llegada':^17}"]
            sep += ["-" * 17]

        if tiene_zona:
            cols += [f"{'Próx. llegada al PS':^20}"]
            sep += ["-" * 20]

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

        if tiene_zona:
            cols += [f"{'Zona':^7}"]
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
            elif evento[2].tipo == TipoEvento.LLEGADA_AL_PS:
                self.procesar_llegada_al_ps(
                    evento[2]
                )  # Procesar el evento de llegada al puesto de servicio (cuando un cliente termina de caminar por la zona de seguridad)
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
        tiene_zona = self.config["tiene_zona_seguridad"]

        vals = [f"{self.tiempo_actual:^15}"]

        if tiene_prioridad:
            vals += [
                f"{self.obtener_proxima_llegada_a():^17}",
                f"{self.obtener_proxima_llegada_b():^17}",
            ]
        else:
            vals += [f"{self.obtener_proxima_llegada():^17}"]

        if tiene_zona:
            vals += [f"{self.obtener_proxima_llegada_al_ps():^20}"]

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

        if tiene_zona:
            vals += [f"{self.sistema.zona_seguridad_ocupada:^7}"]

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
        if tiene_zona:
            grafico += "Z" if self.sistema.zona_seguridad_ocupada else " "
        if tiene_prioridad:
            grafico += "A" * len(self.sistema.cola_A) + "B" * len(self.sistema.cola_B)
        else:
            grafico += "O" * len(self.sistema.cola)

        vals += [f"{grafico:^15}"]

        print("|" + "|".join(vals) + "|")
