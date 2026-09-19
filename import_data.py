"""将 PSEO CSV/Excel 数据导入 MySQL 的 student_placement 表。

使用方式：
1. 将 PSEO 数据文件放到 data/ 目录，或在 .env 中配置 DATA_FILE_PATH。
2. 先运行 python init_db.py 重建表结构。
3. 再运行 python import_data.py 导入数据。

脚本会尽量兼容 PSEO 常见列名，并把缺失字段置为 NULL，便于快速替换数据集。
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "pseo_outcomes.csv"
DATA_FILE_PATH = Path(os.getenv("DATA_FILE_PATH", str(DEFAULT_DATA_PATH)))
if not DATA_FILE_PATH.is_absolute():
    DATA_FILE_PATH = BASE_DIR / DATA_FILE_PATH

PSEO_COLUMNS = [
    "institution_id",
    "institution_name",
    "institution_state",
    "institution_type",
    "degree_level",
    "degree_field",
    "major_category",
    "graduation_year",
    "cohort_year",
    "industry",
    "employment_count",
    "total_graduates",
    "employment_rate",
    "median_earnings_1yr",
    "median_earnings_5yr",
    "median_earnings_10yr",
    "p25_earnings",
    "p75_earnings",
    "source_file",
]

COLUMN_ALIASES = {
    "institution_id": [
        "institution_id", "institution", "inst_id", "unitid", "opeid", "institution code", "school_id", "college_id"
    ],
    "institution_name": [
        "institution_name", "label_institution", "inst_name", "school_name", "name", "college", "college_name"
    ],
    "institution_state": [
        "institution_state", "state", "stabbr", "inst_state", "location_state"
    ],
    "institution_type": [
        "institution_type", "institution_level", "inst_level", "sector", "control"
    ],
    "degree_level": [
        "degree_level", "degree", "credential", "credential_level", "award_level", "level"
    ],
    "degree_field": [
        "degree_field", "field", "major", "cipdesc", "cip_title", "program", "program_name"
    ],
    "major_category": [
        "major_category", "field_category", "cip2", "cip_family", "major_group"
    ],
    "graduation_year": [
        "graduation_year", "grad_year", "year", "cohort", "cohort_year", "grad_cohort"
    ],
    "cohort_year": [
        "cohort_year", "cohort", "grad_cohort", "cohort_label"
    ],
    "industry": [
        "industry", "industry_name", "naics", "naics_desc", "sector_name", "employment_industry"
    ],
    "employment_count": [
        "employment_count", "employed", "employed_count", "grads_emp", "y1_grads_emp", "graduates_employed",
        "y1_grads_earn"
    ],
    "total_graduates": [
        "total_graduates", "graduates", "grad_count", "cohort_count", "n", "total", "y1_grads_nme",
        "y1_ipeds_count"
    ],
    "employment_rate": [
        "employment_rate", "emp_rate", "employment_pct", "employment_percent"
    ],
    "median_earnings_1yr": [
        "median_earnings_1yr", "earnings_1yr", "median_earnings", "y1_p50_earnings", "p50_earnings_1yr"
    ],
    "median_earnings_5yr": [
        "median_earnings_5yr", "earnings_5yr", "y5_p50_earnings", "p50_earnings_5yr"
    ],
    "median_earnings_10yr": [
        "median_earnings_10yr", "earnings_10yr", "y10_p50_earnings", "p50_earnings_10yr"
    ],
    "p25_earnings": [
        "p25_earnings", "y1_p25_earnings", "earnings_p25", "p25"
    ],
    "p75_earnings": [
        "p75_earnings", "y1_p75_earnings", "earnings_p75", "p75"
    ],
}


def get_connection():
    import pymysql

    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "usermessage"),
        charset="utf8mb4",
    )


def _normalize_column_name(column_name: str) -> str:
    return (
        str(column_name)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
        .replace(".", "_")
    )


def _find_source_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized_columns = {_normalize_column_name(col): col for col in df.columns}
    for alias in aliases:
        normalized_alias = _normalize_column_name(alias)
        if normalized_alias in normalized_columns:
            return normalized_columns[normalized_alias]
    return None


def _to_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").round().astype("Int64")


def _to_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_pseo_dataframe(file_path: Path) -> pd.DataFrame:
    file_ext = file_path.suffix.lower()
    if file_ext == ".csv":
        raw_df = pd.read_csv(file_path, encoding="utf-8-sig")
    elif file_ext in [".xlsx", ".xls"]:
        raw_df = pd.read_excel(file_path)
    else:
        raise ValueError(f"不支持的数据文件格式：{file_ext}，请使用 CSV 或 Excel")

    if raw_df.empty:
        raise ValueError("数据文件为空")

    has_explicit_employment_rate = _find_source_column(raw_df, COLUMN_ALIASES["employment_rate"]) is not None
    df = pd.DataFrame(index=raw_df.index)
    for target_col, aliases in COLUMN_ALIASES.items():
        source_col = _find_source_column(raw_df, aliases)
        df[target_col] = raw_df[source_col] if source_col else pd.NA

    numeric_int_cols = ["graduation_year", "employment_count", "total_graduates"]
    numeric_float_cols = [
        "employment_rate",
        "median_earnings_1yr",
        "median_earnings_5yr",
        "median_earnings_10yr",
        "p25_earnings",
        "p75_earnings",
    ]

    for col in numeric_int_cols:
        df[col] = _to_int_series(df[col])
    for col in numeric_float_cols:
        df[col] = _to_float_series(df[col])

    if not has_explicit_employment_rate:
        missing_rate = df["employment_rate"].isna()
        can_calc_rate = (
            missing_rate
            & df["employment_count"].notna()
            & df["total_graduates"].notna()
            & (df["total_graduates"] != 0)
        )
        df.loc[can_calc_rate, "employment_rate"] = (
            df.loc[can_calc_rate, "employment_count"].astype(float)
            * 100.0
            / df.loc[can_calc_rate, "total_graduates"].astype(float)
        )
    df.loc[(df["employment_rate"] < 0) | (df["employment_rate"] > 100), "employment_rate"] = pd.NA

    df["source_file"] = file_path.name
    df = df[PSEO_COLUMNS].astype(object).where(pd.notna(df), None)
    return df


def import_data():
    if not DATA_FILE_PATH.exists():
        print(f"错误：数据文件不存在：{DATA_FILE_PATH}")
        return False

    con = get_connection()
    cursor = con.cursor()

    try:
        print("清空 student_placement 表现有数据...")
        cursor.execute("TRUNCATE TABLE student_placement")

        print(f"读取数据文件：{DATA_FILE_PATH}")
        df = load_pseo_dataframe(DATA_FILE_PATH)

        insert_sql = """
        INSERT INTO student_placement (
            institution_id, institution_name, institution_state, institution_type,
            degree_level, degree_field, major_category, graduation_year, cohort_year,
            industry, employment_count, total_graduates, employment_rate,
            median_earnings_1yr, median_earnings_5yr, median_earnings_10yr,
            p25_earnings, p75_earnings, source_file
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        data_batch = [tuple(row) for row in df[PSEO_COLUMNS].itertuples(index=False, name=None)]

        cursor.executemany(insert_sql, data_batch)
        con.commit()

        cursor.execute("SELECT COUNT(*) FROM student_placement")
        count = cursor.fetchone()[0]
        print(f"数据导入完成，共导入 {count} 条 PSEO 记录")
        return True
    except Exception as e:
        con.rollback()
        print(f"导入失败：{e}")
        return False
    finally:
        cursor.close()
        con.close()


if __name__ == "__main__":
    success = import_data()
    if success:
        print("可以启动后端了：python main.py")
