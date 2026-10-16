from datetime import datetime

import pandas as pd
import pytest

from mibici.dataset import (
    _detect_csv_encoding,
    find_download_links,
    load_station_nomenclature,
    normalize_trip_chunk,
)


def test_detect_csv_encoding_handles_utf8_and_latin1_site_files() -> None:
    assert _detect_csv_encoding(b'"A\xc3\xb1o_de_nacimiento"') == "utf-8-sig"
    assert _detect_csv_encoding(b'"A\xf1o_de_nacimiento"') == "latin-1"


def test_find_download_links_discovers_monthly_csv_and_latest_nomenclature() -> None:
    html = """
    <a href="/site/assets/files/123/datos_abiertos_2024_01.csv">January</a>
    <a href="/site/assets/files/456/datos_abiertos_2024_02-1.csv">February</a>
    <a href="/site/assets/files/789/nomenclatura_2024_01.csv">Old stations</a>
    <a href="/site/assets/files/900/nomenclatura_2024_02.csv">Latest stations</a>
    """

    monthly_links, nomenclature_url = find_download_links(html)

    assert monthly_links[(2024, 1)] == (
        "https://mibici.net/site/assets/files/123/datos_abiertos_2024_01.csv"
    )
    assert monthly_links[(2024, 2)] == (
        "https://mibici.net/site/assets/files/456/datos_abiertos_2024_02-1.csv"
    )
    assert nomenclature_url == (
        "https://mibici.net/site/assets/files/900/nomenclatura_2024_02.csv"
    )


@pytest.mark.parametrize("birth_year_header", ["Año_de_nacimiento", "A}äe_nacimiento"])
def test_normalize_trip_chunk_uses_utf8_station_names_and_typed_dates(
    birth_year_header: str,
) -> None:
    stations = load_station_nomenclature(
        (
            "id,name,latitude,longitude,dpcapacity\n"
            '2,"(GDL-001) C. Niño héroe",20.1,-103.2,15\n'
            '3,"(GDL-002) C. López Cotilla",20.2,-103.3,19\n'
        ).encode()
    )
    chunk = pd.DataFrame(
        {
            "Viaje_Id": [100],
            "Usuario_Id": [200],
            "Género": ["F"],
            birth_year_header: [1995.0],
            "Inicio_del_viaje": ["2024-01-01 12:30:00"],
            "Fin_del_viaje": ["2024-01-01 12:45:00"],
            "Origen_Id": [2],
            "Destino_Id": [3],
        }
    )

    cleaned = normalize_trip_chunk(chunk, stations)

    assert cleaned.loc[0, "origin_station_name"] == "(GDL-001) C. Niño héroe"
    assert cleaned.loc[0, "destination_station_name"] == "(GDL-002) C. López Cotilla"
    assert cleaned.loc[0, "birth_year"] == 1995
    assert cleaned.loc[0, "started_at"] == datetime(2024, 1, 1, 12, 30)
    assert str(cleaned["started_at"].dtype).startswith("datetime64")
    assert cleaned.loc[0, "origin_latitude"] == 20.1
    assert cleaned.loc[0, "destination_capacity"] == 19


def test_load_station_nomenclature_rejects_duplicate_ids() -> None:
    duplicate_ids = (
        b"id,name,latitude,longitude,dpcapacity\n"
        b'2,"Station A",20.1,-103.2,15\n'
        b'2,"Station B",20.2,-103.3,19\n'
    )

    with pytest.raises(ValueError, match="duplicate station IDs"):
        load_station_nomenclature(duplicate_ids)
