"""Reconstruye insumos oficiales con fechas fijas y conserva un manifiesto."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import runpy
import shutil
from datetime import date
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from mibici import dataset
from mibici.config import (PROJ_ROOT, RAW_DATA_DIR, PROCESSED_DATA_DIR,
    P2_TRIPS_PATH, P2_STATIONS_PATH, P2_EXAMPLES_PATH, P2_MOVEMENTS_PATH,
    PROJECT_DATA_START, PROJECT_DATA_END)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""): h.update(block)
    return h.hexdigest()

def prepare(question):
    trips=PROCESSED_DATA_DIR/"trips.parquet"
    stations=RAW_DATA_DIR/"stations_nomenclature.csv"
    if not trips.exists() or not stations.exists():
        original_download=dataset._download
        original_chunks=dataset._read_trip_csv_chunks
        source_urls={}
        def cached_download(url):
            name=url.rsplit("/",1)[-1]
            if name.endswith(".csv"):
                path=RAW_DATA_DIR/name
                if not path.exists():
                    content=original_download(url)
                    path.parent.mkdir(parents=True,exist_ok=True)
                    temporary=path.with_suffix(path.suffix+".download")
                    temporary.write_bytes(content)
                    temporary.replace(path)
                source_urls[name]=url
                return path.read_bytes()
            return original_download(url)
        def cached_chunks(url):
            content=cached_download(url)
            path=RAW_DATA_DIR/url.rsplit("/",1)[-1]
            encoding=dataset._detect_csv_encoding(content.splitlines()[0])
            print("Procesando fuente oficial:",path.name,flush=True)
            yield from pd.read_csv(path,encoding=encoding,chunksize=dataset.CSV_CHUNK_SIZE)
        dataset._download=cached_download
        dataset._read_trip_csv_chunks=cached_chunks
        try:
            start,end=dataset._date_range(date.fromisoformat(PROJECT_DATA_START),date.fromisoformat(PROJECT_DATA_END))
            dataset.download_and_clean(start,end,trips,stations)
        finally:
            dataset._download=original_download
            dataset._read_trip_csv_chunks=original_chunks
        records=[{"archivo":name,"url":url,"bytes":(RAW_DATA_DIR/name).stat().st_size,
                  "sha256":digest(RAW_DATA_DIR/name)} for name,url in sorted(source_urls.items())]
        path=PROJ_ROOT/"data/interim/project_sources_manifest.json"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({"inicio":PROJECT_DATA_START,"fin_inclusivo":PROJECT_DATA_END,
            "procedencia":"Reconstrucción del portal oficial; DVC requiere credenciales no disponibles",
            "fuentes":records,"trips_sha256":digest(trips)},ensure_ascii=False,indent=2))
    if question=="P1":
        runpy.run_path(str(PROJ_ROOT/"notebooks/preparacion_p1.py"),run_name="__main__")
    elif question=="P2":
        if not P2_TRIPS_PATH.exists():
            writer=None
            temporary=P2_TRIPS_PATH.with_suffix(".tmp.parquet")
            try:
                for batch in pq.ParquetFile(trips).iter_batches(batch_size=100000):
                    frame=batch.to_pandas()
                    frame=frame.loc[frame.started_at.ge(pd.Timestamp("2023-11-01"))]
                    if frame.empty:continue
                    table=pa.Table.from_pandas(frame,preserve_index=False)
                    if writer is None:writer=pq.ParquetWriter(temporary,table.schema,compression="zstd")
                    writer.write_table(table)
                if writer is None:raise ValueError("No hay filas para P2")
                writer.close();writer=None;temporary.replace(P2_TRIPS_PATH)
            finally:
                if writer is not None:writer.close()
        if not P2_STATIONS_PATH.exists():shutil.copy2(stations,P2_STATIONS_PATH)
        if not P2_MOVEMENTS_PATH.exists():
            from mibici.build_p2_movements import main
            main()
        if not P2_EXAMPLES_PATH.exists():
            from mibici.build_p2_examples import main
            main()
    print("Insumos preparados:",question,flush=True)
