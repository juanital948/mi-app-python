
from flask import Flask, jsonify
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime, timezone
import logging
import json
import socket

app = Flask(__name__)

APP_NAME = "mi-app-python"

# Metricas para Prometheus
inscripciones = Counter(
    "inscripciones_total",
    "Cantidad de inscripciones realizadas"
)

errores = Counter(
    "errores_total",
    "Cantidad de errores generados"
)

estudiantes = Gauge(
    "estudiantes_registrados",
    "Cantidad de estudiantes registrados"
)

cantidad_estudiantes = 0


# Enviar logs JSON a Logstash por TCP
class LogstashHandler(logging.Handler):
    def emit(self, record):
        evento = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "application": APP_NAME,
            "level": record.levelname,
            "message": record.getMessage()
        }

        try:
            with socket.create_connection(
                ("localhost", 5001), timeout=2
            ) as conexion:
                conexion.sendall(
                    (json.dumps(evento) + "\n").encode("utf-8")
                )
        except OSError:
            print("Logstash no disponible:", evento)


logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(LogstashHandler())


@app.route("/")
def inicio():
    return """
    <h1>Sistema de Inscripcion de Estudiantes</h1>
    <p>Aplicacion de monitoreo - Reto 8</p>
    <a href="/inscribir">Inscribir estudiante</a>
    <br><br>
    <a href="/error">Simular error</a>
    <br><br>
    <a href="/metrics">Ver metricas</a>
    """


@app.route("/inscribir")
def inscribir():
    global cantidad_estudiantes

    cantidad_estudiantes += 1
    inscripciones.inc()
    estudiantes.set(cantidad_estudiantes)

    logger.info("Estudiante inscrito correctamente")

    return jsonify({
        "mensaje": "Inscripcion exitosa",
        "total_estudiantes": cantidad_estudiantes
    })


@app.route("/error")
def generar_error():
    errores.inc()

    logger.error("Error al inscribir estudiante")

    return jsonify({
        "mensaje": "Error simulado en la inscripcion"
    }), 500


@app.route("/metrics")
def metricas():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
