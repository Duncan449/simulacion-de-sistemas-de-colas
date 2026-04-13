from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from Simulacion import Simulacion

app = FastAPI()


class ConfigRequest(BaseModel):
    tiempo_total: int
    tiene_prioridad: bool
    tiene_descanso: bool
    tiene_abandono: bool
    llegada_min: Optional[int] = None
    llegada_max: Optional[int] = None
    llegada_a_min: Optional[int] = None
    llegada_a_max: Optional[int] = None
    llegada_b_min: Optional[int] = None
    llegada_b_max: Optional[int] = None
    servicio_min: int = 1
    servicio_max: int = 1
    salida_min: Optional[int] = None
    salida_max: Optional[int] = None
    descanso_min: Optional[int] = None
    descanso_max: Optional[int] = None
    abandono_a_min: Optional[int] = None
    abandono_a_max: Optional[int] = None
    abandono_b_min: Optional[int] = None
    abandono_b_max: Optional[int] = None


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/simular")
async def simular(config_req: ConfigRequest):
    config = config_req.model_dump()

    # Si no hay prioridad, los generadores A/B deben tener valores válidos
    if not config["tiene_prioridad"]:
        config["llegada_a_min"] = config["llegada_min"]
        config["llegada_a_max"] = config["llegada_max"]
        config["llegada_b_min"] = config["llegada_min"]
        config["llegada_b_max"] = config["llegada_max"]
    else:
        config["llegada_min"] = config["llegada_a_min"]
        config["llegada_max"] = config["llegada_a_max"]

    # Si no hay descanso, los generadores de descanso deben tener valores válidos
    if not config["tiene_descanso"]:
        config["salida_min"] = 1
        config["salida_max"] = 1
        config["descanso_min"] = 1
        config["descanso_max"] = 1

    # Si no hay abandono, los generadores de abandono deben tener valores válidos
    if not config["tiene_abandono"]:
        config["abandono_a_min"] = 1
        config["abandono_a_max"] = 1
        config["abandono_b_min"] = 1
        config["abandono_b_max"] = 1
    elif not config["tiene_prioridad"]:
        config["abandono_b_min"] = config["abandono_a_min"]
        config["abandono_b_max"] = config["abandono_a_max"]

    sim = Simulacion(config["tiempo_total"], config)
    resultados = []

    def capturar_fila():
        tiene_prioridad = config["tiene_prioridad"]
        tiene_descanso = config["tiene_descanso"]
        tiene_abandono = config["tiene_abandono"]

        # Representación gráfica del estado del sistema
        grafico = "⧇" if sim.sistema.puesto_de_servicio else "▢"
        if tiene_descanso:
            grafico += "D" if sim.sistema.servidor else " "
        else:
            grafico += "D"
        if tiene_prioridad:
            grafico += "A" * len(sim.sistema.cola_A) + "B" * len(sim.sistema.cola_B)
        else:
            grafico += "O" * len(sim.sistema.cola)

        fila = {
            "tiempo_actual": sim.tiempo_actual,
            "proxima_llegada": (
                sim.obtener_proxima_llegada() if not tiene_prioridad else None
            ),
            "proxima_llegada_a": (
                sim.obtener_proxima_llegada_a() if tiene_prioridad else None
            ),
            "proxima_llegada_b": (
                sim.obtener_proxima_llegada_b() if tiene_prioridad else None
            ),
            "proximo_fin_servicio": sim.obtener_proximo_fin_servicio(),
            "proximo_descanso": (
                sim.obtener_proximo_descanso() if tiene_descanso else None
            ),
            "proximo_trabajo": (
                sim.obtener_proximo_trabajo() if tiene_descanso else None
            ),
            "proximo_abandono": (
                sim.obtener_proximo_abandono()
                if tiene_abandono and not tiene_prioridad
                else None
            ),
            "proximo_abandono_a": (
                sim.obtener_proximo_abandono_a()
                if tiene_abandono and tiene_prioridad
                else None
            ),
            "proximo_abandono_b": (
                sim.obtener_proximo_abandono_b()
                if tiene_abandono and tiene_prioridad
                else None
            ),
            "puesto_de_servicio": sim.sistema.puesto_de_servicio,
            "cola": len(sim.sistema.cola) if not tiene_prioridad else None,
            "cola_a": len(sim.sistema.cola_A) if tiene_prioridad else None,
            "cola_b": len(sim.sistema.cola_B) if tiene_prioridad else None,
            "servidor": sim.sistema.servidor if tiene_descanso else None,
            "grafico": grafico,
        }
        resultados.append(fila)

    sim._imprimir_fila = capturar_fila
    sim._imprimir_encabezado = lambda: None

    sim.inicio()
    sim.ejecutar()

    return {"config": config, "filas": resultados}
