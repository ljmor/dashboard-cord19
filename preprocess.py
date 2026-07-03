"""
Preprocesamiento del corpus CORD-19 (metadata.csv) -> parquet ligero solo 2021.

Replica EXACTAMENTE el criterio del notebook (Fase IV):
  - Se conservan solo los registros cuyo `publish_time` corresponde a 2021.
  - Se derivan: title_len, abstract_len, n_authors, publish_month y banderas
    de completitud (has_abstract, has_doi, has_pmcid, has_journal).

El CSV pesa ~860 MB (~600k filas), por eso se procesa por bloques (chunks) y
se guarda un parquet de pocos MB que el dashboard carga cacheado y al instante.

Uso:
    python preprocess.py
"""
from __future__ import annotations
import os
import sys
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(AQUI, "context", "metadata.csv")
DIR_DATA = os.path.join(AQUI, "data")
RUTA_PARQUET = os.path.join(DIR_DATA, "cord19_2021.parquet")

# Columnas originales que necesitamos leer del CSV (las demás se ignoran)
USECOLS = [
    "cord_uid", "source_x", "title", "doi", "pmcid",
    "abstract", "publish_time", "authors", "journal", "license",
]

# Columnas finales del dataset ligero (idénticas al df_eda del notebook + license)
COLS_FINALES = [
    "cord_uid", "source_x", "journal", "license", "publish_month",
    "title_len", "abstract_len", "n_authors",
    "has_abstract", "has_doi", "has_pmcid", "has_journal",
]


def procesar_bloque(bloque: pd.DataFrame) -> pd.DataFrame:
    """Filtra a 2021 y deriva las variables del EDA para un chunk."""
    pt = bloque["publish_time"].astype("string")

    # Año y mes desde publish_time (regex idéntico al del notebook)
    anio = pt.str.extract(r"(\d{4})", expand=False)
    mes = pt.str.extract(r"\d{4}-(\d{2})", expand=False)

    bloque = bloque.assign(
        publish_year=pd.to_numeric(anio, errors="coerce"),
        publish_month=pd.to_numeric(mes, errors="coerce"),
    )

    # Solo 2021
    bloque = bloque[bloque["publish_year"] == 2021].copy()
    if bloque.empty:
        return bloque

    bloque["title_len"] = bloque["title"].str.len()
    bloque["abstract_len"] = bloque["abstract"].str.len()
    bloque["n_authors"] = (
        bloque["authors"].fillna("").apply(
            lambda a: 0 if a == "" else len(str(a).split(";"))
        )
    )
    bloque["has_abstract"] = bloque["abstract"].notna().astype("int8")
    bloque["has_doi"] = bloque["doi"].notna().astype("int8")
    bloque["has_pmcid"] = bloque["pmcid"].notna().astype("int8")
    bloque["has_journal"] = bloque["journal"].notna().astype("int8")

    return bloque[COLS_FINALES]


def main() -> None:
    if not os.path.exists(RUTA_CSV):
        sys.exit(f"ERROR: no se encontró el CSV en {RUTA_CSV}")

    os.makedirs(DIR_DATA, exist_ok=True)
    print(f"Leyendo {RUTA_CSV} por bloques ...")

    partes = []
    total_filas = 0
    lector = pd.read_csv(
        RUTA_CSV,
        usecols=USECOLS,
        dtype="string",
        chunksize=100_000,
        engine="c",
        on_bad_lines="skip",
    )
    for i, bloque in enumerate(lector, 1):
        total_filas += len(bloque)
        parte = procesar_bloque(bloque)
        if not parte.empty:
            partes.append(parte)
        print(f"  bloque {i:>3}  |  filas leídas: {total_filas:>9,}  |  "
              f"2021 acumulado: {sum(len(p) for p in partes):>8,}")

    if not partes:
        sys.exit("No se encontraron registros de 2021.")

    df = pd.concat(partes, ignore_index=True)

    # Tipos compactos para un parquet pequeño y rápido
    df["publish_month"] = df["publish_month"].astype("Int8")
    df["title_len"] = df["title_len"].astype("Int32")
    df["abstract_len"] = df["abstract_len"].astype("Int32")
    df["n_authors"] = df["n_authors"].astype("Int32")
    for c in ("source_x", "journal", "license"):
        df[c] = df[c].astype("string")

    df.to_parquet(RUTA_PARQUET, index=False, compression="snappy")

    mb = os.path.getsize(RUTA_PARQUET) / 1e6
    print("\n" + "=" * 60)
    print(f"Listo. Registros 2021: {len(df):,}")
    print(f"Parquet guardado en: {RUTA_PARQUET}  ({mb:.1f} MB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
