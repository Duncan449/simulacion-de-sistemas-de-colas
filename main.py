from Simulacion import Simulacion


def pedir_int(mensaje, minimo=1):
    while True:
        try:
            valor = int(input(mensaje))
            if valor >= minimo:
                return valor
            print(f"  Ingresá un número mayor o igual a {minimo}.")
        except ValueError:
            print("  Valor inválido, ingresá un número entero.")


def pedir_rango(nombre):
    print(f"\n  Tiempo de {nombre} — ¿constante o aleatorio?")
    print("    1) Constante")
    print("    2) Aleatorio (distribución uniforme)")
    opcion = input("  Opción: ").strip()
    if opcion == "1":
        valor = pedir_int(f"  Valor constante para {nombre}: ", minimo=1)
        return valor, valor
    else:
        minimo = pedir_int(f"  Valor mínimo para {nombre}: ", minimo=1)
        maximo = pedir_int(
            f"  Valor máximo para {nombre} (>= {minimo}): ", minimo=minimo
        )
        return minimo, maximo


if __name__ == "__main__":
    print("=" * 60)
    print("       SIMULACIÓN DE SISTEMA DE COLAS")
    print("=" * 60)

    tiempo_total = pedir_int("\nTiempo total de simulación (en segundos): ", minimo=1)

    # ── Tipos de clientes y prioridad ──────────────────────────
    print("\n--- Tipos de clientes ---")
    print("¿Hay dos tipos de clientes (A y B) con prioridad?")
    print("  1) No — un solo tipo de cliente")
    print("  2) Sí — clientes tipo A (prioridad alta) y tipo B")
    tiene_prioridad = input("Opción: ").strip() == "2"

    if tiene_prioridad:
        llegada_a_min, llegada_a_max = pedir_rango("llegada de clientes tipo A")
        llegada_b_min, llegada_b_max = pedir_rango("llegada de clientes tipo B")
        llegada_min = llegada_max = None
    else:
        llegada_min, llegada_max = pedir_rango("llegada de clientes")
        llegada_a_min = llegada_a_max = llegada_b_min = llegada_b_max = None

    # ── Tiempo de servicio ─────────────────────────────────────
    print("\n--- Tiempo de servicio ---")
    servicio_min, servicio_max = pedir_rango("servicio")

    # ── Descanso del servidor ──────────────────────────────────
    print("\n--- Servidor ---")
    print("¿El servidor puede ausentarse?")
    print("  1) No")
    print("  2) Sí")
    tiene_descanso = input("Opción: ").strip() == "2"

    salida_min = salida_max = descanso_min = descanso_max = None
    if tiene_descanso:
        salida_min, salida_max = pedir_rango("tiempo hasta que el servidor se ausenta")
        descanso_min, descanso_max = pedir_rango("duración del descanso del servidor")

    # ── Abandono de clientes ───────────────────────────────────
    print("\n--- Abandono ---")
    print("¿Los clientes pueden abandonar la cola si esperan demasiado?")
    print("  1) No")
    print("  2) Sí")
    tiene_abandono = input("Opción: ").strip() == "2"

    abandono_a_min = abandono_a_max = abandono_b_min = abandono_b_max = None
    if tiene_abandono:
        if tiene_prioridad:
            abandono_a_min, abandono_a_max = pedir_rango(
                "tiempo de paciencia de clientes tipo A"
            )
            abandono_b_min, abandono_b_max = pedir_rango(
                "tiempo de paciencia de clientes tipo B"
            )
        else:
            abandono_a_min, abandono_a_max = pedir_rango(
                "tiempo de paciencia de los clientes"
            )
            abandono_b_min, abandono_b_max = (
                abandono_a_min,
                abandono_a_max,
            )  # Se usa el mismo para ambos en modo general

    # ── Armar configuración y lanzar simulación ────────────────
    config = {
        "tiene_prioridad": tiene_prioridad,
        "tiene_descanso": tiene_descanso,
        "tiene_abandono": tiene_abandono,
        "llegada_min": llegada_min,
        "llegada_max": llegada_max,
        "llegada_a_min": llegada_a_min,
        "llegada_a_max": llegada_a_max,
        "llegada_b_min": llegada_b_min,
        "llegada_b_max": llegada_b_max,
        "servicio_min": servicio_min,
        "servicio_max": servicio_max,
        "salida_min": salida_min,
        "salida_max": salida_max,
        "descanso_min": descanso_min,
        "descanso_max": descanso_max,
        "abandono_a_min": abandono_a_min,
        "abandono_a_max": abandono_a_max,
        "abandono_b_min": abandono_b_min,
        "abandono_b_max": abandono_b_max,
    }

    print("\n" + "=" * 60)
    print("Iniciando simulación...")
    print("=" * 60 + "\n")

    simulacion = Simulacion(
        tiempo_total, config
    )  # Crear una instancia de la simulación
    simulacion.inicio()  # Iniciar la simulación
    simulacion.ejecutar()  # Ejecutar la simulación
