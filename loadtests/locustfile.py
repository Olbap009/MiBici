"""Carga reproducible de inferencia P2 con los tres escenarios de la interfaz."""

from locust import HttpUser, between, task

SCENARIOS = [
    {
        "departures_prev_30m": 2,
        "arrivals_prev_30m": 1,
        "departures_prev_2h": 8,
        "arrivals_prev_2h": 6,
        "hour": 10,
        "minute": 30,
        "day_of_week": 2,
        "capacity": 15,
    },
    {
        "departures_prev_30m": 14,
        "arrivals_prev_30m": 1,
        "departures_prev_2h": 35,
        "arrivals_prev_2h": 4,
        "hour": 8,
        "minute": 0,
        "day_of_week": 1,
        "capacity": 15,
    },
    {
        "departures_prev_30m": 1,
        "arrivals_prev_30m": 15,
        "departures_prev_2h": 3,
        "arrivals_prev_2h": 40,
        "hour": 18,
        "minute": 30,
        "day_of_week": 4,
        "capacity": 15,
    },
]
LABELS = {"sin_presion_neta_elevada", "presion_sin_bicicletas", "presion_sin_anclajes"}


class PredictionUser(HttpUser):
    wait_time = between(0.1, 0.3)

    def on_start(self):
        self.scenario_index = 0

    @task
    def predict(self):
        payload = SCENARIOS[self.scenario_index % len(SCENARIOS)]
        self.scenario_index += 1
        with self.client.post("/predict", json=payload, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}")
                return
            try:
                if response.json().get("prediction") not in LABELS:
                    response.failure("Predicción ajena al contrato P2")
            except ValueError:
                response.failure("Respuesta JSON inválida")
