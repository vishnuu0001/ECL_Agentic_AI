import os, json, random, string, yaml, pandas as pd
from typing import Dict, Any
from providers.ollama_cli import OllamaCLI

def _load_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _prompt_template(n: int) -> str:
    here = os.path.join(os.path.dirname(__file__), "..", "prompts", "sas_prompt.txt")
    with open(here, "r", encoding="utf-8") as f:
        t = f.read()
    return t.replace("{{N_RECORDS}}", str(n))

def _validate_and_flatten(payload: Dict[str, Any]) -> pd.DataFrame:
    if not isinstance(payload, dict) or "records" not in payload:
        raise ValueError("Invalid payload: missing 'records'")
    rows = []
    for r in payload.get("records", []):
        rows.append({
            "exposure_id": str(r.get("exposure_id","")).strip() or _rand_id(),
            "segment": r.get("segment","Retail"),
            "country": r.get("country","DE"),
            "stage": int(r.get("stage",1)),
            "EAD": float(r.get("EAD",0.0)),
            "LGD": float(r.get("LGD",0.45)),
            "PD_12m": float(r.get("PD_12m",0.02)),
            "PD_lifetime": float(r.get("PD_lifetime",0.05)),
            "discount_rate": float(r.get("discount_rate",0.07)),
            "source": "ollama"
        })
    return pd.DataFrame(rows)

def _rand_id():
    import random, string
    return "EXP-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _fallback_generate(n: int, seed: int = 42):
    random.seed(seed)
    rows = []
    segs = ["Retail","SME","Corporate"]
    countries = ["DE","FR","IT","ES","CN","UK","US"]
    for i in range(n):
        seg = random.choice(segs)
        EAD = round(random.uniform(1e4, 5e6), 2)
        LGD = round(random.uniform(0.2, 0.6), 4)
        pd12 = round(random.uniform(0.01, 0.08), 4)
        pdlife = round(max(pd12, pd12 + random.uniform(0.0, 0.07)), 4)
        rows.append({
            "exposure_id": _rand_id(),
            "segment": seg,
            "country": random.choice(countries),
            "stage": random.choice([1,1,1,2,2,3]),
            "EAD": EAD,
            "LGD": LGD,
            "PD_12m": pd12,
            "PD_lifetime": pdlife,
            "discount_rate": round(random.uniform(0.05, 0.12), 4),
            "source": "fallback"
        })
    import pandas as pd
    return pd.DataFrame(rows)

def run(config_path: str = "config.yaml", n: int = None, model: str = None, out_dir: str = None) -> Dict[str, Any]:
    cfg = _load_cfg(config_path)
    work = out_dir or cfg.get("workspace","./workspace")
    os.makedirs(work, exist_ok=True)

    nrec = int(n or cfg.get("sas_defaults",{}).get("n_records", 20))
    tmpl = _prompt_template(nrec)

    try:
        provider = OllamaCLI(
            model=(model or cfg.get("ollama",{}).get("model","llama3.1:8b-instruct")),
            temperature=float(cfg.get("ollama",{}).get("temperature",0.2)),
            max_tokens=int(cfg.get("ollama",{}).get("max_tokens",1024)),
        )
        text = provider.generate_json(tmpl)
        # Try strict parse; if fails try to salvage JSON substring
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            import re
            m = re.search(r'\{.*\}', text, flags=re.S)
            if not m:
                raise
            payload = json.loads(m.group(0))
        df = _validate_and_flatten(payload)
    except Exception:
        # Fallback synthetic data (still marks 'source': 'fallback')
        seed = int(cfg.get("sas_defaults",{}).get("seed", 42))
        df = _fallback_generate(nrec, seed=seed)
        payload = {"meta":{"source_system":"SAS-Fallback","currency":"EUR"}, "records": df.to_dict(orient="records")}

    # persist
    with open(os.path.join(work, "sas_output.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    df.to_csv(os.path.join(work, "sas_output.csv"), index=False)

    return {"ok": True, "rows": len(df), "workspace": work}
