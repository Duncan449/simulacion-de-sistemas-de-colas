#Arrancar la simulación con un tiempo total de 28800 unidades de tiempo
from Simulacion import Simulacion
if __name__ == "__main__":
    tiempo_total = 288  # Tiempo total de la simulación (8 horas)
    simulacion = Simulacion(tiempo_total)  # Crear una instancia de la simulación
    simulacion.inicio_prioridad()  # Iniciar la simulación
    simulacion.ejecutar_con_prioridad()  # Ejecutar la simulación