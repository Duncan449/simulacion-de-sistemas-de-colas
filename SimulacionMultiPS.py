from Evento import Evento, TipoEvento
from Cliente import Cliente
import heapq
import random


class PuestoDeServicio:
    """Representa un puesto de servicio individual dentro del sistema multi-PS."""

    def __init__(self, id_ps, config_ps):
        self.id_ps = id_ps
        self.config = config_ps
        self.ocupado = False  # True si hay un cliente siendo atendido
        self.servidor_presente = True  # False si el servidor está de descanso
        self.zona_seguridad_ocupada = (
            False  # True si hay un cliente caminando hacia este PS
        )
        self.tiempo_fin_servicio = (
            None  # Tiempo programado para el fin del servicio actual
        )
        self.tiempo_restante_servicio = (
            None  # Tiempo restante si el servidor se ausenta
        )


class SimulacionMultiPS:
    """Simulación de sistema de colas con múltiples puestos de servicio y cola compartida."""

    def __init__(self, tiempo_total, config_global, configs_ps):
        """
        Args:
            tiempo_total: Duración total de la simulación.
            config_global: Config compartida (llegadas, abandono, prioridad).
            configs_ps: Lista de configs individuales por PS (servicio, descanso, zona).
        """
        self.tiempo_total = tiempo_total
        self.config_global = config_global
        self.configs_ps = configs_ps
        self.n_ps = len(configs_ps)

        self.tiempo_actual = 0
        self.eventos = []
        self.contador_eventos = 0
        self.contador_clientes = 0

        # ── Puestos de servicio ────────────────────────────────────────────────
        self.puestos = [PuestoDeServicio(i, configs_ps[i]) for i in range(self.n_ps)]

        # ── Cola compartida ────────────────────────────────────────────────────
        self.cola = []  # Cola general (sin prioridad)
        self.cola_A = []  # Cola tipo A (con prioridad)
        self.cola_B = []  # Cola tipo B (con prioridad)

        # ── Métricas globales ──────────────────────────────────────────────────
        self.clientes_atendidos = 0
        self.clientes_atendidos_a = 0
        self.clientes_atendidos_b = 0
        self.clientes_abandonaron = 0
        self.clientes_abandonaron_a = 0
        self.clientes_abandonaron_b = 0
        self.tiempos_espera = []
        self.tiempos_espera_a = []
        self.tiempos_espera_b = []

        # ── Métricas por PS ────────────────────────────────────────────────────
        self.tiempo_ocupado_ps = [0] * self.n_ps
        self.tiempo_ausente_ps = [0] * self.n_ps
        self.cantidad_descansos_ps = [0] * self.n_ps
        self._tiempo_inicio_servicio_ps = [None] * self.n_ps
        self._tiempo_inicio_ausencia_ps = [None] * self.n_ps
        self.evento_actual = None  # Para imprimir el evento actual en la tabla

        # ── Cliente actual por PS ──────────────────────────────────────────────
        self.cliente_actual_ps = [None] * self.n_ps

        # ── Aplicar vector inicial ─────────────────────────────────────────────
        self._aplicar_vector_inicial()

    # ── Generadores de tiempo globales ────────────────────────────────────────

    def generar_tiempo_llegada(self):
        min_ = self.config_global["llegada_min"]
        max_ = self.config_global["llegada_max"]
        return random.randint(min_, max_) if min_ != max_ else min_

    def generar_tiempo_llegada_a(self):
        min_ = self.config_global["llegada_a_min"]
        max_ = self.config_global["llegada_a_max"]
        return random.randint(min_, max_) if min_ != max_ else min_

    def generar_tiempo_llegada_b(self):
        min_ = self.config_global["llegada_b_min"]
        max_ = self.config_global["llegada_b_max"]
        return random.randint(min_, max_) if min_ != max_ else min_

    def generar_tiempo_abandono_a(self):
        min_ = self.config_global.get("abandono_a_min", 0) or 0
        max_ = self.config_global.get("abandono_a_max", 0) or 0
        return random.randint(min_, max_)

    def generar_tiempo_abandono_b(self):
        min_ = self.config_global.get("abandono_b_min", 0) or 0
        max_ = self.config_global.get("abandono_b_max", 0) or 0
        return random.randint(min_, max_)

    # ── Generadores de tiempo por PS ───────────────────────────────────────────

    def generar_tiempo_servicio(self, id_ps):
        cfg = self.configs_ps[id_ps]
        min_ = cfg["servicio_min"]
        max_ = cfg["servicio_max"]
        return random.randint(min_, max_) if min_ != max_ else min_

    def generar_tiempo_salida_servidor(self, id_ps):
        cfg = self.configs_ps[id_ps]
        min_ = cfg["salida_min"]
        max_ = cfg["salida_max"]
        return random.randint(min_, max_) if min_ != max_ else min_

    def generar_tiempo_llegada_servidor(self, id_ps):
        cfg = self.configs_ps[id_ps]
        min_ = cfg["descanso_min"]
        max_ = cfg["descanso_max"]
        return random.randint(min_, max_) if min_ != max_ else min_

    def generar_tiempo_caminata(self, id_ps):
        cfg = self.configs_ps[id_ps]
        min_ = cfg.get("caminata_min", 0) or 0
        max_ = cfg.get("caminata_max", 0) or 0
        return random.randint(min_, max_) if min_ != max_ else min_

    # ── Auxiliares de cola ─────────────────────────────────────────────────────

    def _cola_tiene_clientes(self):
        if self.config_global["tiene_prioridad"]:
            return bool(self.cola_A or self.cola_B)
        return bool(self.cola)

    def _sacar_siguiente_de_cola(self):
        """Retorna (cliente, tipo)."""
        if self.config_global["tiene_prioridad"]:
            if self.cola_A:
                return self.cola_A.pop(0), "A"
            return self.cola_B.pop(0), "B"
        return self.cola.pop(0), "general"

    def _primer_ps_libre(self):
        """Retorna el índice del primer PS libre y con servidor presente, o None."""
        for i, ps in enumerate(self.puestos):
            if (
                not ps.ocupado
                and ps.servidor_presente
                and not ps.zona_seguridad_ocupada
            ):
                return i
        return None

    def _programar_abandono(self, cliente, tiempo_abandono):
        ev = Evento(TipoEvento.ABANDONO, self.tiempo_actual + tiempo_abandono)
        ev.id_cliente = cliente.id
        heapq.heappush(
            self.eventos,
            (self.tiempo_actual + tiempo_abandono, self.contador_eventos, ev),
        )
        self.contador_eventos += 1

    def _invalidar_abandono(self, id_cliente):
        for i in range(len(self.eventos)):
            if (
                self.eventos[i][2].tipo == TipoEvento.ABANDONO
                and self.eventos[i][2].id_cliente == id_cliente
            ):
                self.eventos[i][2].valido = False
                break

    # ── Iniciar servicio en un PS ──────────────────────────────────────────────

    def _iniciar_servicio_en_ps(self, id_ps):
        """Programa el fin de servicio en el PS indicado."""
        ps = self.puestos[id_ps]
        ps.ocupado = True
        tiempo_servicio = self.generar_tiempo_servicio(id_ps)
        ev = Evento(TipoEvento.FIN_SERVICIO_PS, self.tiempo_actual + tiempo_servicio)
        ev.id_ps = id_ps
        ps.tiempo_fin_servicio = self.tiempo_actual + tiempo_servicio
        heapq.heappush(
            self.eventos,
            (self.tiempo_actual + tiempo_servicio, self.contador_eventos, ev),
        )
        self.contador_eventos += 1
        self._tiempo_inicio_servicio_ps[id_ps] = self.tiempo_actual

    def _enviar_cliente_a_zona(self, cliente, id_ps):
        """Envía un cliente a la zona de seguridad del PS indicado."""
        ps = self.puestos[id_ps]
        ps.zona_seguridad_ocupada = True
        tiempo_caminata = self.generar_tiempo_caminata(id_ps)
        ev = Evento(TipoEvento.LLEGADA_AL_PS_PS, self.tiempo_actual + tiempo_caminata)
        ev.id_ps = id_ps
        ev.id_cliente = cliente.id
        heapq.heappush(
            self.eventos,
            (self.tiempo_actual + tiempo_caminata, self.contador_eventos, ev),
        )
        self.contador_eventos += 1

    def _asignar_cliente_a_ps(self, cliente, tipo_cliente, id_ps):
        """Asigna un cliente a un PS libre, registrando su tiempo de espera."""
        tiene_zona = self.configs_ps[id_ps]["tiene_zona_seguridad"]
        tiene_abandono = self.config_global["tiene_abandono"]

        tiempo_espera = self.tiempo_actual - cliente.hora_llegada
        self.tiempos_espera.append(tiempo_espera)
        if tipo_cliente == "A":
            self.tiempos_espera_a.append(tiempo_espera)
        elif tipo_cliente == "B":
            self.tiempos_espera_b.append(tiempo_espera)

        if tiene_abandono:
            self._invalidar_abandono(cliente.id)

        self.cliente_actual_ps[id_ps] = cliente

        if tiene_zona:
            self._enviar_cliente_a_zona(cliente, id_ps)
        else:
            self._iniciar_servicio_en_ps(id_ps)

    # ── Aplicar vector inicial ─────────────────────────────────────────────────

    def _aplicar_vector_inicial(self):
        vi_global = self.config_global.get("vector_inicial", {}) or {}
        tiene_prioridad = self.config_global["tiene_prioridad"]
        tiene_abandono = self.config_global["tiene_abandono"]

        # ── Cola inicial compartida ────────────────────────────────────────────
        if tiene_prioridad:
            cantidad_a = vi_global.get("cola_a_cantidad", 0) or 0
            tiempos_a = vi_global.get("cola_a_tiempos", []) or []
            for i in range(cantidad_a):
                espera = tiempos_a[i] if i < len(tiempos_a) else 0
                cliente = Cliente(self.contador_clientes, -espera, "A")
                self.cola_A.append(cliente)
                self.contador_clientes += 1
                if tiene_abandono:
                    pt = self.generar_tiempo_abandono_a()
                    tr = max(1, pt - espera)
                    ev = Evento(TipoEvento.ABANDONO, tr)
                    ev.id_cliente = cliente.id
                    heapq.heappush(self.eventos, (tr, self.contador_eventos, ev))
                    self.contador_eventos += 1

            cantidad_b = vi_global.get("cola_b_cantidad", 0) or 0
            tiempos_b = vi_global.get("cola_b_tiempos", []) or []
            for i in range(cantidad_b):
                espera = tiempos_b[i] if i < len(tiempos_b) else 0
                cliente = Cliente(self.contador_clientes, -espera, "B")
                self.cola_B.append(cliente)
                self.contador_clientes += 1
                if tiene_abandono:
                    pt = self.generar_tiempo_abandono_b()
                    tr = max(1, pt - espera)
                    ev = Evento(TipoEvento.ABANDONO, tr)
                    ev.id_cliente = cliente.id
                    heapq.heappush(self.eventos, (tr, self.contador_eventos, ev))
                    self.contador_eventos += 1
        else:
            cantidad = vi_global.get("cola_cantidad", 0) or 0
            tiempos = vi_global.get("cola_tiempos", []) or []
            for i in range(cantidad):
                espera = tiempos[i] if i < len(tiempos) else 0
                cliente = Cliente(self.contador_clientes, -espera, "general")
                self.cola.append(cliente)
                self.contador_clientes += 1
                if tiene_abandono:
                    pt = self.generar_tiempo_abandono_a()
                    tr = max(1, pt - espera)
                    ev = Evento(TipoEvento.ABANDONO, tr)
                    ev.id_cliente = cliente.id
                    heapq.heappush(self.eventos, (tr, self.contador_eventos, ev))
                    self.contador_eventos += 1

        # ── Estado inicial por PS ──────────────────────────────────────────────
        for id_ps, ps in enumerate(self.puestos):
            vi_ps = self.configs_ps[id_ps].get("vector_inicial", {}) or {}

            # Servidor
            if self.configs_ps[id_ps]["tiene_descanso"]:
                servidor_presente = vi_ps.get("servidor_presente", True)
                ps.servidor_presente = servidor_presente
                if not servidor_presente:
                    tiempo_regreso = vi_ps.get("tiempo_regreso_servidor", 0) or 0
                    if tiempo_regreso > 0:
                        ev = Evento(TipoEvento.LLEGADA_SERVIDOR_PS, tiempo_regreso)
                        ev.id_ps = id_ps
                        heapq.heappush(
                            self.eventos, (tiempo_regreso, self.contador_eventos, ev)
                        )
                        self.contador_eventos += 1
                    self._tiempo_inicio_ausencia_ps[id_ps] = 0

            # PS ocupado
            ps_ocupado = vi_ps.get("ps_ocupado", False)
            if ps_ocupado:
                ps.ocupado = True
                tiempo_restante = vi_ps.get("ps_tiempo_restante", 0) or 0
                if tiempo_restante > 0:
                    cliente_ps = Cliente(self.contador_clientes, 0, "general")
                    self.contador_clientes += 1
                    self.cliente_actual_ps[id_ps] = cliente_ps
                    ps.tiempo_fin_servicio = tiempo_restante
                    ev = Evento(TipoEvento.FIN_SERVICIO_PS, tiempo_restante)
                    ev.id_ps = id_ps
                    heapq.heappush(
                        self.eventos, (tiempo_restante, self.contador_eventos, ev)
                    )
                    self.contador_eventos += 1
                    self._tiempo_inicio_servicio_ps[id_ps] = 0

            # Zona de seguridad
            if self.configs_ps[id_ps]["tiene_zona_seguridad"]:
                zona_ocupada = vi_ps.get("zona_ocupada", False)
                if zona_ocupada:
                    ps.zona_seguridad_ocupada = True
                    tiempo_llegada_ps = vi_ps.get("tiempo_llegada_ps", 0) or 0
                    if tiempo_llegada_ps > 0:
                        cliente_zona = Cliente(self.contador_clientes, 0, "general")
                        self.contador_clientes += 1
                        self.cliente_actual_ps[id_ps] = cliente_zona
                        ev = Evento(TipoEvento.LLEGADA_AL_PS_PS, tiempo_llegada_ps)
                        ev.id_ps = id_ps
                        ev.id_cliente = cliente_zona.id
                        heapq.heappush(
                            self.eventos, (tiempo_llegada_ps, self.contador_eventos, ev)
                        )
                        self.contador_eventos += 1

        # ── Si hay cola y PS libres al inicio, asignar ─────────────────────────
        while self._cola_tiene_clientes():
            id_ps = self._primer_ps_libre()
            if id_ps is None:
                break
            cliente, tipo = self._sacar_siguiente_de_cola()
            self._asignar_cliente_a_ps(cliente, tipo, id_ps)

    # ── Obtención de próximos eventos ──────────────────────────────────────────

    def obtener_proxima_llegada(self):
        for ev in self.eventos:
            if ev[2].tipo == TipoEvento.LLEGADA:
                return ev[0]
        return ""

    def obtener_proxima_llegada_a(self):
        for ev in self.eventos:
            if ev[2].tipo == TipoEvento.LLEGADA_A:
                return ev[0]
        return ""

    def obtener_proxima_llegada_b(self):
        for ev in self.eventos:
            if ev[2].tipo == TipoEvento.LLEGADA_B:
                return ev[0]
        return ""

    def obtener_proximo_fin_servicio(self, id_ps):
        for ev in self.eventos:
            if (
                ev[2].tipo == TipoEvento.FIN_SERVICIO_PS
                and ev[2].valido
                and ev[2].id_ps == id_ps
            ):
                return ev[0]
        ps = self.puestos[id_ps]
        if (
            not ps.servidor_presente
            and ps.ocupado
            and ps.tiempo_restante_servicio is not None
        ):
            hora_regreso = self.obtener_proximo_trabajo(id_ps)
            if hora_regreso != "":
                return hora_regreso + ps.tiempo_restante_servicio
        return ""

    def obtener_proximo_descanso(self, id_ps):
        for ev in self.eventos:
            if ev[2].tipo == TipoEvento.SALIDA_SERVIDOR_PS and ev[2].id_ps == id_ps:
                return ev[0]
        return ""

    def obtener_proximo_trabajo(self, id_ps):
        for ev in self.eventos:
            if ev[2].tipo == TipoEvento.LLEGADA_SERVIDOR_PS and ev[2].id_ps == id_ps:
                return ev[0]
        return ""

    def obtener_proxima_llegada_al_ps(self, id_ps):
        for ev in self.eventos:
            if (
                ev[2].tipo == TipoEvento.LLEGADA_AL_PS_PS
                and ev[2].valido
                and ev[2].id_ps == id_ps
            ):
                return ev[0]
        return ""

    def obtener_proximo_abandono(self):
        ids_cola = [c.id for c in self.cola]
        for ev in self.eventos:
            if (
                ev[2].tipo == TipoEvento.ABANDONO
                and ev[2].valido
                and ev[2].id_cliente in ids_cola
            ):
                return ev[0]
        return ""

    def obtener_proximo_abandono_a(self):
        ids = [c.id for c in self.cola_A]
        for ev in self.eventos:
            if (
                ev[2].tipo == TipoEvento.ABANDONO
                and ev[2].valido
                and ev[2].id_cliente in ids
            ):
                return ev[0]
        return ""

    def obtener_proximo_abandono_b(self):
        ids = [c.id for c in self.cola_B]
        for ev in self.eventos:
            if (
                ev[2].tipo == TipoEvento.ABANDONO
                and ev[2].valido
                and ev[2].id_cliente in ids
            ):
                return ev[0]
        return ""

    # ── Procesadores de eventos ────────────────────────────────────────────────

    def _procesar_llegada_cliente(self, cliente, tipo_cliente):
        """Lógica común al llegar un cliente: asignar a PS libre o encolar."""
        tiene_abandono = self.config_global["tiene_abandono"]
        id_ps = self._primer_ps_libre()

        if id_ps is not None:
            # Hay PS libre: asignar directamente
            self.tiempos_espera.append(0)
            if tipo_cliente == "A":
                self.tiempos_espera_a.append(0)
            elif tipo_cliente == "B":
                self.tiempos_espera_b.append(0)
            self.cliente_actual_ps[id_ps] = cliente
            tiene_zona = self.configs_ps[id_ps]["tiene_zona_seguridad"]
            if tiene_zona:
                self._enviar_cliente_a_zona(cliente, id_ps)
            else:
                self._iniciar_servicio_en_ps(id_ps)
        else:
            # Todos los PS ocupados: encolar
            if self.config_global["tiene_prioridad"]:
                if tipo_cliente == "A":
                    self.cola_A.append(cliente)
                else:
                    self.cola_B.append(cliente)
            else:
                self.cola.append(cliente)

            if tiene_abandono:
                tiempo_abandono = (
                    self.generar_tiempo_abandono_a()
                    if tipo_cliente != "B"
                    else self.generar_tiempo_abandono_b()
                )
                self._programar_abandono(cliente, tiempo_abandono)

    def procesar_llegada(self, evento):
        nuevo_cliente = Cliente(self.contador_clientes, self.tiempo_actual, "general")
        self.contador_clientes += 1
        self._procesar_llegada_cliente(nuevo_cliente, "general")

        vi = self.config_global.get("vector_inicial", {}) or {}
        tiempo = vi.get("primera_llegada") or self.generar_tiempo_llegada()
        # Limpiar primera_llegada para que solo aplique una vez
        if "primera_llegada" in (self.config_global.get("vector_inicial") or {}):
            self.config_global["vector_inicial"]["primera_llegada"] = None

        ev = Evento(TipoEvento.LLEGADA, self.tiempo_actual + tiempo)
        heapq.heappush(
            self.eventos, (self.tiempo_actual + tiempo, self.contador_eventos, ev)
        )
        self.contador_eventos += 1

    def procesar_llegada_a(self, evento):
        nuevo_cliente = Cliente(self.contador_clientes, self.tiempo_actual, "A")
        self.contador_clientes += 1
        self._procesar_llegada_cliente(nuevo_cliente, "A")

        tiempo = self.generar_tiempo_llegada_a()
        ev = Evento(TipoEvento.LLEGADA_A, self.tiempo_actual + tiempo)
        heapq.heappush(
            self.eventos, (self.tiempo_actual + tiempo, self.contador_eventos, ev)
        )
        self.contador_eventos += 1

    def procesar_llegada_b(self, evento):
        nuevo_cliente = Cliente(self.contador_clientes, self.tiempo_actual, "B")
        self.contador_clientes += 1
        self._procesar_llegada_cliente(nuevo_cliente, "B")

        tiempo = self.generar_tiempo_llegada_b()
        ev = Evento(TipoEvento.LLEGADA_B, self.tiempo_actual + tiempo)
        heapq.heappush(
            self.eventos, (self.tiempo_actual + tiempo, self.contador_eventos, ev)
        )
        self.contador_eventos += 1

    def procesar_llegada_al_ps(self, evento):
        """Cliente termina de caminar por la zona y llega al PS."""
        id_ps = evento.id_ps
        ps = self.puestos[id_ps]
        ps.zona_seguridad_ocupada = False  # La zona queda libre
        self._iniciar_servicio_en_ps(id_ps)

    def procesar_fin_servicio(self, evento):
        id_ps = evento.id_ps
        ps = self.puestos[id_ps]
        cliente_que_termina = self.cliente_actual_ps[id_ps]

        # Registrar métricas
        self.clientes_atendidos += 1
        if cliente_que_termina is not None:
            if cliente_que_termina.tipo == "A":
                self.clientes_atendidos_a += 1
            elif cliente_que_termina.tipo == "B":
                self.clientes_atendidos_b += 1

        # Registrar ocupación del PS
        if self._tiempo_inicio_servicio_ps[id_ps] is not None:
            self.tiempo_ocupado_ps[id_ps] += (
                self.tiempo_actual - self._tiempo_inicio_servicio_ps[id_ps]
            )
            self._tiempo_inicio_servicio_ps[id_ps] = None

        ps.ocupado = False
        ps.tiempo_fin_servicio = None
        self.cliente_actual_ps[id_ps] = None

        # Si hay clientes en cola, asignar el siguiente a este PS
        if self._cola_tiene_clientes():
            cliente, tipo = self._sacar_siguiente_de_cola()
            self._asignar_cliente_a_ps(cliente, tipo, id_ps)

    def procesar_salida_servidor(self, evento):
        id_ps = evento.id_ps
        ps = self.puestos[id_ps]
        ps.servidor_presente = False
        self._tiempo_inicio_ausencia_ps[id_ps] = self.tiempo_actual
        self.cantidad_descansos_ps[id_ps] += 1

        # Invalidar el fin de servicio actual si el PS está ocupado
        if ps.tiempo_fin_servicio is not None:
            for i in range(len(self.eventos)):
                if (
                    self.eventos[i][2].tipo == TipoEvento.FIN_SERVICIO_PS
                    and self.eventos[i][2].id_ps == id_ps
                    and self.eventos[i][0] == ps.tiempo_fin_servicio
                ):
                    self.eventos[i][2].valido = False
                    break
            ps.tiempo_restante_servicio = ps.tiempo_fin_servicio - self.tiempo_actual
            ps.tiempo_fin_servicio = None

        # Programar regreso del servidor
        tiempo_regreso = self.generar_tiempo_llegada_servidor(id_ps)
        ev = Evento(TipoEvento.LLEGADA_SERVIDOR_PS, self.tiempo_actual + tiempo_regreso)
        ev.id_ps = id_ps
        heapq.heappush(
            self.eventos,
            (self.tiempo_actual + tiempo_regreso, self.contador_eventos, ev),
        )
        self.contador_eventos += 1

    def procesar_llegada_servidor(self, evento):
        id_ps = evento.id_ps
        ps = self.puestos[id_ps]
        ps.servidor_presente = True

        # Registrar tiempo de ausencia
        if self._tiempo_inicio_ausencia_ps[id_ps] is not None:
            self.tiempo_ausente_ps[id_ps] += (
                self.tiempo_actual - self._tiempo_inicio_ausencia_ps[id_ps]
            )
            self._tiempo_inicio_ausencia_ps[id_ps] = None

        if ps.ocupado and ps.tiempo_restante_servicio is not None:
            # Reanudar servicio interrumpido
            tiempo_fin = self.tiempo_actual + ps.tiempo_restante_servicio
            ev = Evento(TipoEvento.FIN_SERVICIO_PS, tiempo_fin)
            ev.id_ps = id_ps
            ps.tiempo_fin_servicio = tiempo_fin
            heapq.heappush(self.eventos, (tiempo_fin, self.contador_eventos, ev))
            self.contador_eventos += 1
            ps.tiempo_restante_servicio = None
            self._tiempo_inicio_servicio_ps[id_ps] = self.tiempo_actual

        elif not ps.ocupado and self._cola_tiene_clientes():
            # PS libre y hay cola: atender siguiente
            cliente, tipo = self._sacar_siguiente_de_cola()
            self._asignar_cliente_a_ps(cliente, tipo, id_ps)

        # Programar próximo descanso
        tiempo_salida = self.generar_tiempo_salida_servidor(id_ps)
        ev = Evento(TipoEvento.SALIDA_SERVIDOR_PS, self.tiempo_actual + tiempo_salida)
        ev.id_ps = id_ps
        heapq.heappush(
            self.eventos,
            (self.tiempo_actual + tiempo_salida, self.contador_eventos, ev),
        )
        self.contador_eventos += 1

    def procesar_abandono(self, evento):
        tiene_prioridad = self.config_global["tiene_prioridad"]
        id_cliente = evento.id_cliente

        if tiene_prioridad:
            for cola, tipo in [(self.cola_A, "A"), (self.cola_B, "B")]:
                ids = [c.id for c in cola]
                if id_cliente in ids:
                    cliente = next(c for c in cola if c.id == id_cliente)
                    cola.remove(cliente)
                    self.clientes_abandonaron += 1
                    if tipo == "A":
                        self.clientes_abandonaron_a += 1
                    else:
                        self.clientes_abandonaron_b += 1
                    return
        else:
            ids = [c.id for c in self.cola]
            if id_cliente in ids:
                cliente = next(c for c in self.cola if c.id == id_cliente)
                self.cola.remove(cliente)
                self.clientes_abandonaron += 1

    # ── Métricas ───────────────────────────────────────────────────────────────

    def obtener_metricas(self):
        tiene_prioridad = self.config_global["tiene_prioridad"]

        def promedio(lista):
            return round(sum(lista) / len(lista), 2) if lista else 0

        def maximo(lista):
            return max(lista) if lista else 0

        metricas = {
            "clientes_atendidos": self.clientes_atendidos,
            "clientes_abandonaron": self.clientes_abandonaron,
            "espera_promedio": promedio(self.tiempos_espera),
            "espera_maxima": maximo(self.tiempos_espera),
            "por_ps": [],
        }

        if tiene_prioridad:
            metricas["clientes_atendidos_a"] = self.clientes_atendidos_a
            metricas["clientes_atendidos_b"] = self.clientes_atendidos_b
            metricas["clientes_abandonaron_a"] = self.clientes_abandonaron_a
            metricas["clientes_abandonaron_b"] = self.clientes_abandonaron_b
            metricas["espera_promedio_a"] = promedio(self.tiempos_espera_a)
            metricas["espera_promedio_b"] = promedio(self.tiempos_espera_b)
            metricas["espera_maxima_a"] = maximo(self.tiempos_espera_a)
            metricas["espera_maxima_b"] = maximo(self.tiempos_espera_b)

        for id_ps in range(self.n_ps):
            ocupacion = (
                round((self.tiempo_ocupado_ps[id_ps] / self.tiempo_total) * 100, 1)
                if self.tiempo_total > 0
                else 0
            )
            ps_metricas = {
                "id": id_ps + 1,
                "nombre": self.configs_ps[id_ps].get("nombre", f"PS{id_ps + 1}"),
                "clientes_atendidos": sum(
                    1 for _ in range(self.clientes_atendidos)
                ),  # placeholder
                "ocupacion": ocupacion,
                "tiempo_ocupado": round(self.tiempo_ocupado_ps[id_ps], 2),
                "cantidad_descansos": self.cantidad_descansos_ps[id_ps],
            }
            if self.configs_ps[id_ps]["tiene_descanso"]:
                ps_metricas["tiempo_ausente"] = round(self.tiempo_ausente_ps[id_ps], 2)
            metricas["por_ps"].append(ps_metricas)

        return metricas

    # ── Inicio ─────────────────────────────────────────────────────────────────

    def inicio(self):
        tiene_prioridad = self.config_global["tiene_prioridad"]
        vi = self.config_global.get("vector_inicial", {}) or {}

        if tiene_prioridad:
            tiempo_a = vi.get("primera_llegada_a") or self.generar_tiempo_llegada_a()
            ev_a = Evento(TipoEvento.LLEGADA_A, tiempo_a)
            heapq.heappush(self.eventos, (tiempo_a, self.contador_eventos, ev_a))
            self.contador_eventos += 1

            tiempo_b = vi.get("primera_llegada_b") or self.generar_tiempo_llegada_b()
            ev_b = Evento(TipoEvento.LLEGADA_B, tiempo_b)
            heapq.heappush(self.eventos, (tiempo_b, self.contador_eventos, ev_b))
            self.contador_eventos += 1
        else:
            tiempo = vi.get("primera_llegada") or self.generar_tiempo_llegada()
            ev = Evento(TipoEvento.LLEGADA, tiempo)
            heapq.heappush(self.eventos, (tiempo, self.contador_eventos, ev))
            self.contador_eventos += 1

        # Programar primer descanso de cada PS (si aplica y servidor presente)
        for id_ps, ps in enumerate(self.puestos):
            if self.configs_ps[id_ps]["tiene_descanso"] and ps.servidor_presente:
                tiempo_salida = self.generar_tiempo_salida_servidor(id_ps)
                ev = Evento(TipoEvento.SALIDA_SERVIDOR_PS, tiempo_salida)
                ev.id_ps = id_ps
                heapq.heappush(self.eventos, (tiempo_salida, self.contador_eventos, ev))
                self.contador_eventos += 1

        # Imprimir t=0
        self.evento_actual = None
        self._imprimir_fila()

    # ── Ejecutar ───────────────────────────────────────────────────────────────

    def ejecutar(self):
        while self.eventos:
            evento = heapq.heappop(self.eventos)
            if not evento[2].valido:
                continue
            if evento[0] > self.tiempo_total:
                break

            self.tiempo_actual = evento[0]
            tipo = evento[2].tipo
            self.evento_actual = tipo  # Registrar el tipo de evento actual


            if tipo == TipoEvento.LLEGADA:
                self.procesar_llegada(evento[2])
            elif tipo == TipoEvento.LLEGADA_A:
                self.procesar_llegada_a(evento[2])
            elif tipo == TipoEvento.LLEGADA_B:
                self.procesar_llegada_b(evento[2])
            elif tipo == TipoEvento.LLEGADA_AL_PS_PS:
                self.procesar_llegada_al_ps(evento[2])
            elif tipo == TipoEvento.FIN_SERVICIO_PS:
                self.procesar_fin_servicio(evento[2])
            elif tipo == TipoEvento.SALIDA_SERVIDOR_PS:
                self.procesar_salida_servidor(evento[2])
            elif tipo == TipoEvento.LLEGADA_SERVIDOR_PS:
                self.procesar_llegada_servidor(evento[2])
            elif tipo == TipoEvento.ABANDONO:
                self.procesar_abandono(evento[2])

            self._imprimir_fila()

    # ── Imprimir fila ──────────────────────────────────────────────────────────

    def _imprimir_fila(self):
        tiene_prioridad = self.config_global["tiene_prioridad"]
        tiene_abandono = self.config_global["tiene_abandono"]

        if tiene_prioridad:
            llegada = f"{self.obtener_proxima_llegada_a():^12} / {self.obtener_proxima_llegada_b():^12}"
        else:
            llegada = f"{self.obtener_proxima_llegada():^15}"

        cola_str = ""
        if tiene_prioridad:
            cola_str = f"A:{len(self.cola_A)} B:{len(self.cola_B)}"
        else:
            cola_str = str(len(self.cola))

        ps_str = " | ".join(
            f"PS{i+1}:{'⧇' if ps.ocupado else '▢'}"
            f"{'D' if ps.servidor_presente else ' '}"
            f"{'Z' if ps.zona_seguridad_ocupada else ' '}"
            for i, ps in enumerate(self.puestos)
        )

        print(
            f"t={self.tiempo_actual:>6} | Llegada:{llegada} | Cola:{cola_str:>6} | {ps_str}"
        )
