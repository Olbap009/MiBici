"""Transformaciones reutilizables para el proyecto MiBici."""

import numpy as np
import pandas as pd

from mibici.config import P2_INTERVAL_MINUTES


def aggregate_p2_movements(
    trips: pd.DataFrame,
    valid_station_ids: set[int],
    interval_minutes: int = P2_INTERVAL_MINUTES,
) -> pd.DataFrame:
    """Cuenta salidas y llegadas por estación e intervalo.

    Excluye viajes con fechas faltantes o duración no positiva.
    Cada extremo se valida por separado para conservar movimientos
    de estaciones válidas aunque el otro extremo no sea modelable.

    Esta función produce conteos observados, no predictores históricos.
    Los intervalos sin eventos no se generan aquí.
    """
    if interval_minutes <= 0:
        raise ValueError("El intervalo debe ser positivo.")

    columns = [
        "started_at",
        "ended_at",
        "origin_station_id",
        "destination_station_id",
    ]
    data = trips.loc[:, columns].copy()

    for column in ("started_at", "ended_at"):
        data[column] = pd.to_datetime(data[column], errors="raise")

    # Regla inicial documentada: conservar solo duración positiva.
    valid_time = (
        data["started_at"].notna()
        & data["ended_at"].notna()
        & (data["ended_at"] > data["started_at"])
    )
    data = data.loc[valid_time]
    counts = []

    # Una salida usa la hora de inicio; una llegada, la hora de fin.
    for station_column, time_column, count_name in (
        ("origin_station_id", "started_at", "departures"),
        ("destination_station_id", "ended_at", "arrivals"),
    ):
        valid_side = data[station_column].isin(valid_station_ids)
        events = data.loc[valid_side, [station_column, time_column]].copy()

        events = events.rename(columns={station_column: "station_id"})
        events["interval_start"] = events[time_column].dt.floor(f"{interval_minutes}min")

        grouped = events.groupby(["station_id", "interval_start"]).size().rename(count_name)
        counts.append(grouped)

    # Unimos salidas y llegadas del mismo intervalo.
    result = pd.concat(counts, axis=1).fillna(0)
    result = result.astype({"departures": "int64", "arrivals": "int64"})

    return result.reset_index().sort_values(["station_id", "interval_start"], ignore_index=True)


def build_p2_station_examples(
    movements: pd.DataFrame,
    capacity: float,
    start: str,
    end: str,
) -> pd.DataFrame:
    """Construye predictores históricos y etiqueta para una sola estación.

    start es inclusivo y end exclusivo. Solo deben abarcar cobertura conocida.
    Los ceros representan ausencia de movimientos válidos registrados,
    no disponibilidad real ni confirmación de que la estación estaba abierta.
    """
    import numpy as np

    from mibici.config import P2_ACTIVITY_DAYS, P2_PRESSURE_THRESHOLD

    if not np.isfinite(capacity) or capacity <= 0:
        raise ValueError("La capacidad debe ser positiva y finita.")
    if movements["station_id"].nunique() != 1:
        raise ValueError("La función requiere exactamente una estación.")
    if movements["interval_start"].duplicated().any():
        raise ValueError("Hay intervalos duplicados para esta estación.")

    station_id = int(movements["station_id"].iloc[0])
    step = pd.Timedelta(minutes=P2_INTERVAL_MINUTES)
    start_time, end_time = pd.Timestamp(start), pd.Timestamp(end)

    if (
        start_time >= end_time
        or start_time != start_time.floor(f"{P2_INTERVAL_MINUTES}min")
        or end_time != end_time.floor(f"{P2_INTERVAL_MINUTES}min")
    ):
        raise ValueError("Los límites deben ser válidos y alineados al intervalo.")

    calendar = pd.date_range(
        start_time,
        end_time,
        freq=step,
        inclusive="left",
    )

    # Cada fila representa el intervalo [t, t + 30 minutos).
    grid = (
        movements.set_index("interval_start")[["departures", "arrivals"]]
        .reindex(calendar, fill_value=0)
        .astype("int64")
    )

    # shift(1) excluye los movimientos del intervalo que vamos a predecir.
    previous = grid.shift(1)
    examples = pd.DataFrame(index=calendar)
    examples["departures_prev_30m"] = previous["departures"]
    examples["arrivals_prev_30m"] = previous["arrivals"]

    two_hours = 120 // P2_INTERVAL_MINUTES
    for column in ("departures", "arrivals"):
        examples[f"{column}_prev_2h"] = (
            previous[column].rolling(two_hours, min_periods=two_hours).sum()
        )

    activity_windows = P2_ACTIVITY_DAYS * 24 * 60 // P2_INTERVAL_MINUTES
    historical_activity = (
        grid.sum(axis=1).shift(1).rolling(activity_windows, min_periods=activity_windows).sum()
    )

    examples["hour"] = calendar.hour
    examples["minute"] = calendar.minute
    examples["day_of_week"] = calendar.dayofweek
    examples["capacity"] = float(capacity)

    # Estas cantidades futuras se usan exclusivamente para crear la etiqueta.
    pressure = (grid["departures"] - grid["arrivals"]) / capacity
    examples["target"] = np.select(
        [
            pressure >= P2_PRESSURE_THRESHOLD,
            pressure <= -P2_PRESSURE_THRESHOLD,
        ],
        ["presion_sin_bicicletas", "presion_sin_anclajes"],
        default="sin_presion_neta_elevada",
    )

    # Exigimos historia completa y actividad previa, nunca actividad futura.
    eligible = historical_activity.notna() & historical_activity.gt(0)
    examples = examples.loc[eligible].copy()

    examples.insert(0, "station_id", station_id)
    examples.index.name = "prediction_time"
    examples = examples.reset_index()
    examples["target_end"] = examples["prediction_time"] + step
    return examples


def extract_p3_station_features(
    trips: pd.DataFrame,
    nomenclature: pd.DataFrame,
) -> pd.DataFrame:
    """Extrae la matriz de características por estación para la segmentación no supervisada (P3).

    Esta función calcula métricas consolidadas que definen el perfil funcional
    y la tipología de movilidad de cada estación en el AMG.

    Variables extraídas y pertinencia:
    - viajes_promedio_diario: Volumen medio diario de viajes iniciados.
      Pertinencia: Diferencia estaciones nodales de alto flujo de estaciones de baja densidad.
    - viajes_desviacion_diaria: Variabilidad del uso diario.
      Pertinencia: Captura la estabilidad o volatilidad de la demanda interdiaria.
    - pct_pico_matutino: Fracción de salidas entre 07:00 y 09:59 hrs.
      Pertinencia: Identifica estaciones residenciales o expulsoras matutinas.
    - pct_mediodia: Fracción de salidas entre 12:00 y 15:59 hrs.
      Pertinencia: Caracteriza zonas comerciales, educativas o de servicios.
    - pct_pico_vespertino: Fracción de salidas entre 17:00 y 20:59 hrs.
      Pertinencia: Identifica polos de empleo y zonas corporativas (retorno vespertino).
    - pct_fin_semana: Proporción de viajes en sábados y domingos sobre el total.
      Pertinencia: Separa corredores recreativos de estaciones puramente laborales.
    - ratio_flujo_neto: Saldo relativo (Llegadas - Salidas) / (Llegadas + Salidas).
      Pertinencia: Revela si la estación es un atractor neto (> 0) o emisor neto (< 0).
    - capacidad: Número total de anclajes físicos disponibles.
      Pertinencia: Factor de escala estructural para evaluar dimensionamiento urbano.
    - latitude, longitude: Coordenadas espaciales WGS84.
      Pertinencia: Garantiza coherencia geográfica y contigüidad territorial.
    """
    df = trips.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["started_at"]):
        df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")

    # Filtro de registros válidos
    valid = df["started_at"].notna() & df["origin_station_id"].notna()
    df = df.loc[valid]

    # Componentes temporales
    df["date"] = df["started_at"].dt.floor("D")
    df["hour"] = df["started_at"].dt.hour
    df["is_weekend"] = df["started_at"].dt.dayofweek >= 5

    # 1. Viajes diarios y promedios por estación de origen
    daily = df.groupby(["origin_station_id", "date"]).size()
    daily_mean = daily.groupby("origin_station_id").mean().rename("viajes_promedio_diario")
    daily_std = (
        daily.groupby("origin_station_id").std().fillna(0).rename("viajes_desviacion_diaria")
    )
    total_dep = df["origin_station_id"].value_counts().rename("total_salidas")

    # 2. Perfil por bloques horarios
    hourly = df.groupby(["origin_station_id", "hour"]).size().unstack(fill_value=0)
    hourly_total = hourly.sum(axis=1).replace(0, np.nan)

    morning_hours = [h for h in [7, 8, 9] if h in hourly.columns]
    midday_hours = [h for h in [12, 13, 14, 15] if h in hourly.columns]
    evening_hours = [h for h in [17, 18, 19, 20] if h in hourly.columns]

    pct_morning = (hourly[morning_hours].sum(axis=1) / hourly_total).rename("pct_pico_matutino")
    pct_midday = (hourly[midday_hours].sum(axis=1) / hourly_total).rename("pct_mediodia")
    pct_evening = (hourly[evening_hours].sum(axis=1) / hourly_total).rename("pct_pico_vespertino")

    # 3. Uso en fin de semana
    weekend = df.groupby(["origin_station_id", "is_weekend"]).size().unstack(fill_value=0)
    if True in weekend.columns and False in weekend.columns:
        pct_weekend = (weekend[True] / (weekend[True] + weekend[False])).rename("pct_fin_semana")
    else:
        pct_weekend = pd.Series(0.0, index=daily_mean.index, name="pct_fin_semana")

    # 4. Flujo neto (Llegadas vs Salidas)
    total_arr = df["destination_station_id"].value_counts().rename("total_llegadas")

    # Consolidación inicial de métricas
    features = pd.DataFrame(index=daily_mean.index)
    features = features.join(
        [daily_mean, daily_std, total_dep, pct_morning, pct_midday, pct_evening, pct_weekend]
    ).fillna(0)
    features = features.join(total_arr).fillna(0)
    features["ratio_flujo_neto"] = (features["total_llegadas"] - features["total_salidas"]) / (
        features["total_llegadas"] + features["total_salidas"] + 1e-6
    )

    # 5. Fusión con nomenclatura
    nom = nomenclature.copy()
    id_col = next((c for c in ("id", "station_id", "id_estacion") if c in nom.columns), "id")
    cap_col = next(
        (c for c in ("dpcapacity", "capacity", "capacidad") if c in nom.columns), "dpcapacity"
    )
    name_col = next((c for c in ("name", "station_name", "nombre") if c in nom.columns), "name")

    nom_subset = nom[[id_col, name_col, "latitude", "longitude", cap_col]].copy()
    nom_subset = nom_subset.rename(
        columns={
            id_col: "station_id",
            name_col: "nombre",
            cap_col: "capacidad",
        }
    )
    nom_subset["station_id"] = nom_subset["station_id"].astype(features.index.dtype)

    result = features.merge(nom_subset, left_index=True, right_on="station_id", how="inner")
    result = result.set_index("station_id")
    return result
