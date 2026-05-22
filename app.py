from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List

from Simulacion import Simulacion

app = FastAPI()

# Modelo compartido
class VectorInicial(BaseModel):
    ps_ocupado: bool = False
    ps_tiempo_restante: Optional[int] = None
    servidor_presente: bool = True
    tiempo_regreso_servidor: Optional[int] = None
    zona_ocupada: bool = False
    tiempo_llegada_ps: Optional[int] = None
    cola_cantidad: Optional[int] = None
    cola_tiempos: Optional[List[int]] = None
    cola_a_cantidad: Optional[int] = None
    cola_a_tiempos: Optional[List[int]] = None
    cola_b_cantidad: Optional[int] = None
    cola_b_tiempos: Optional[List[int]] = None
    primera_llegada: Optional[int] = None  
    primera_llegada_a: Optional[int] = None  
    primera_llegada_b: Optional[int] = None  
    
# Modelo modo un servidor
class ConfigRequest(BaseModel):
    tiempo_total: int
    tiene_prioridad: bool
    tiene_descanso: bool
    tiene_abandono: bool
    tiene_zona_seguridad: bool
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
    caminata_min: Optional[int] = None
    caminata_max: Optional[int] = None
    vector_inicial: Optional[VectorInicial] = None


# Modelo modo multi-subsistemas 
class SubsistemaConfig(BaseModel):
    nombre: str = "Subsistema"
    tiene_prioridad: bool = False
    tiene_descanso: bool = False
    tiene_abandono: bool = False
    tiene_zona_seguridad: bool = False
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
    caminata_min: Optional[int] = None
    caminata_max: Optional[int] = None
    vector_inicial: Optional[VectorInicial] = None


class MultiConfigRequest(BaseModel):
    tiempo_total: int
    subsistemas: List[SubsistemaConfig]


# Helpers
def normalizar_config(config: dict) -> dict:
    #Completa los valores faltantes del config para que los generadores no fallen.
    if not config["tiene_prioridad"]:
        config["llegada_a_min"] = config["llegada_min"]
        config["llegada_a_max"] = config["llegada_max"]
        config["llegada_b_min"] = config["llegada_min"]
        config["llegada_b_max"] = config["llegada_max"]
    else:
        config["llegada_min"] = config["llegada_a_min"]
        config["llegada_max"] = config["llegada_a_max"]

    if not config["tiene_descanso"]:
        config["salida_min"] = 1
        config["salida_max"] = 1
        config["descanso_min"] = 1
        config["descanso_max"] = 1

    if not config["tiene_abandono"]:
        config["abandono_a_min"] = 1
        config["abandono_a_max"] = 1
        config["abandono_b_min"] = 1
        config["abandono_b_max"] = 1
    elif not config["tiene_prioridad"]:
        config["abandono_b_min"] = config["abandono_a_min"]
        config["abandono_b_max"] = config["abandono_a_max"]

    if not config.get("tiene_zona_seguridad", False):
        config["caminata_min"] = 0
        config["caminata_max"] = 0

    if config.get("vector_inicial") is None:
        config["vector_inicial"] = {}

    return config


def ejecutar_simulacion(config: dict) -> dict:
    #Crea y ejecuta una simulación, capturando filas y métricas.
    sim = Simulacion(config["tiempo_total"], config)
    resultados = []

    def capturar_fila():
        tiene_prioridad = config["tiene_prioridad"]
        tiene_descanso = config["tiene_descanso"]
        tiene_abandono = config["tiene_abandono"]
        tiene_zona = config["tiene_zona_seguridad"]

        grafico = "⧇" if sim.sistema.puesto_de_servicio else "▢"
        if tiene_descanso:
            grafico += "D" if sim.sistema.servidor else " "
        else:
            grafico += "D"
        if tiene_zona:
            grafico += "Z" if sim.sistema.zona_seguridad_ocupada else " "
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
            "proxima_llegada_al_ps": (
                sim.obtener_proxima_llegada_al_ps() if tiene_zona else None
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
            "zona_seguridad": (
                sim.sistema.zona_seguridad_ocupada if tiene_zona else None
            ),
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

    return {"config": config, "filas": resultados, "metricas": sim.obtener_metricas()}


# Endpoints
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/simular")
async def simular(config_req: ConfigRequest):
    config = config_req.model_dump()
    config = normalizar_config(config)
    return ejecutar_simulacion(config)


@app.post("/simular_multi")
async def simular_multi(req: MultiConfigRequest):
    resultados = []
    for sub in req.subsistemas:
        config = sub.model_dump()
        config["tiempo_total"] = req.tiempo_total
        config = normalizar_config(config)
        resultado = ejecutar_simulacion(config)
        resultado["nombre"] = sub.nombre
        resultados.append(resultado)
    return {"tiempo_total": req.tiempo_total, "subsistemas": resultados}
