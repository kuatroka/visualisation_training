from pathlib import Path
import pandas as pd
import numpy as np
import polars as pl
import duckdb
import os
import pandera as pa
import io

FROM_EXPERIMENT_CSV_IN = Path(
    r"E:\app_data\dropbox_13f_files\processed_tables\TR_02_EXP_SELECT_CIK_CSV"
)
TO_EXPERIMENT_PARQUET = Path(
    r"E:\app_data\dropbox_13f_files\processed_tables\TR_03_EXP_SELECT_CIK_PARQUET"
)

REDUCED_SELECT_CSV = Path(
    r"E:\app_data\dropbox_13f_files\processed_tables\TR_02_EXP_SELECT_CIK_CSV_REDUCED"
)

# ----
processed_tables_copy = Path(
    r"E:\app_data\dropbox_13f_files\processed_tables\processed_tables_copy"
)
processed_tables_copy_reduced = Path(
    r"E:\app_data\dropbox_13f_files\processed_tables\processed_tables_copy_reduced"
)


columns = [
    "cik",
    "cusip8",
    "cusip9",
    "value",
    "shares",
    "rdate",
    "fdate",
    "address",
    "form",
    "shrsOrPrnAmt",
    "putCall",
    "nameOfIssuer",
    "titleOfClass",
    "type",
    "dsource",
]

dtypes = {
    "cusip8": str,
    "cusip9": str,
    "titleOfClass": str,
    "form": str,
    "putCall": str,
    "shrsOrPrnAmt": str,
    "value": pl.Float64,
    "shares": pl.Float64,
    "nameOfIssuer": str,
    "cik": pl.Int64,
    "address": str,
    "type": str,
    "num5": str,
    "deviation": str,
    "shrout": str,
    "num3": str,
    "num2": str,
    "num6": str,
    "num7": str,
    "num4": str,
    "votingAuthority": str,
    "in_universe": str,
    "prc": str,
    "split": str,
    "investmentDiscretion": str,
    "rdate": str,
    "fdate": str,
    "dsource": str,
}

pd_dtypes = {
    "cusip8": str,
    "cusip9": str,
    "titleOfClass": str,
    "form": "category",
    "putCall": "category",
    "shrsOrPrnAmt": "category",
    "value": "float64",
    "shares": "float64",
    "type": "category",
    "nameOfIssuer": str,
    "cik": "int64",
    "address": "category",
    "dsource": "category",
}

# pd_dtypes_validation = {'cusip8': str, 'cusip9': str , 'titleOfClass': str, 'form': 'category', 'putCall': 'category',
#            'shrsOrPrnAmt': 'category', 'value': 'Int64', 'shares': 'Int64', 'type': 'category', 'nameOfIssuer': str,
#            'cik' : 'int64', 'address': 'category',  'dsource': 'category'}


for file in processed_tables_copy.rglob("*.csv"):
    new_file_name = file.parts[-2] + "-" + file.name
    new_file_path = Path(os.path.join(processed_tables_copy_reduced, new_file_name))
    if new_file_path.exists():
        continue

    schema = pl.scan_csv(file).schema
    read_cols = list(set(schema.keys()).intersection(columns))
    df = pl.read_csv(file, columns=read_cols, dtypes=dtypes, low_memory=True)
    for col in columns:
        if col not in df.columns:
            df = df.with_column(pl.lit(None, dtype=dtypes[col]).alias(col))
    # df = df.select(columns)
    df = df.with_columns(
        [
            pl.col("rdate").str.strptime(pl.Date, fmt="%Y%m%d"),
            pl.col("fdate").str.strptime(pl.Date, fmt="%Y%m%d"),
            pl.col("cusip8").str.to_uppercase(),
            pl.col("cusip9").str.to_uppercase(),
            pl.lit("dropbox").alias("dsource"),
        ]
    ).select(columns)

    df.write_csv(new_file_path, sep=",")

    # df = df.to_pandas().astype(pd_dtypes).to_csv(new_file_path,index=False)
