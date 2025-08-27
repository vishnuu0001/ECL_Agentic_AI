import os, json, yaml, pandas as pd
from typing import Dict, Any

def _load_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _load_sas(work: str) -> pd.DataFrame:
    p = os.path.join(work, "sas_output.csv")
    if not os.path.exists(p):
        raise FileNotFoundError(f"Missing {p}. Run generate-sas first.")
    return pd.read_csv(p)

def _calc(df: pd.DataFrame) -> pd.DataFrame:
    # Basic IFRS-9 style ECL:
    # ECL_12m = EAD * PD_12m * LGD
    # ECL_lifetime = EAD * PD_lifetime * LGD
    out = df.copy()
    out["ECL_12m"] = out["EAD"] * out["PD_12m"] * out["LGD"]
    out["ECL_lifetime"] = out["EAD"] * out["PD_lifetime"] * out["LGD"]
    return out

def _summarize(df: pd.DataFrame, group_by: str = None) -> Dict[str, Any]:
    if group_by and group_by in df.columns:
        g = df.groupby(group_by)[["EAD","ECL_12m","ECL_lifetime"]].sum().reset_index()
        return {"group_by": group_by, "groups": g.to_dict(orient="records")}
    totals = df[["EAD","ECL_12m","ECL_lifetime"]].sum().to_dict()
    return {"totals": totals}

def run(config_path: str = "config.yaml", out_dir: str = None, group_by: str = None) -> Dict[str, Any]:
    cfg = _load_cfg(config_path)
    work = out_dir or cfg.get("workspace","./workspace")
    os.makedirs(work, exist_ok=True)

    raw = _load_sas(work)
    calc = _calc(raw)
    calc.to_csv(os.path.join(work, "ecl_results.csv"), index=False)

    summary = _summarize(calc, group_by=group_by)
    with open(os.path.join(work, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return {"ok": True, "rows": len(calc), **summary}
