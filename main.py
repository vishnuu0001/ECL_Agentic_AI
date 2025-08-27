import argparse, json
from agents import sas_agent, risk_agent

def main():
    ap = argparse.ArgumentParser(description="Agentic SAS->Risk (CLI, no UI/localhost)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate-sas", help="Use Ollama to produce Sample SAS data (JSON+CSV)")
    g.add_argument("--config", default="config.yaml")
    g.add_argument("--n", type=int, default=None, help="Number of records to request")
    g.add_argument("--model", default=None, help="Ollama model override (e.g., mistral, llama3.1:8b-instruct)")
    g.add_argument("--out-dir", default=None)

    r = sub.add_parser("calc-risk", help="Compute ECL from SAS outputs")
    r.add_argument("--config", default="config.yaml")
    r.add_argument("--out-dir", default=None)
    r.add_argument("--group-by", default=None, help="Optional grouping column (e.g., segment)")

    a = sub.add_parser("run-all", help="End-to-end: generate SAS then calculate risk")
    a.add_argument("--config", default="config.yaml")
    a.add_argument("--n", type=int, default=None)
    a.add_argument("--model", default=None)
    a.add_argument("--out-dir", default=None)
    a.add_argument("--group-by", default=None)

    args = ap.parse_args()

    if args.cmd == "generate-sas":
        res = sas_agent.run(config_path=args.config, n=args.n, model=args.model, out_dir=args.out_dir)
        print(json.dumps(res, indent=2))
    elif args.cmd == "calc-risk":
        res = risk_agent.run(config_path=args.config, out_dir=args.out_dir, group_by=args.group_by)
        print(json.dumps(res, indent=2))
    elif args.cmd == "run-all":
        res1 = sas_agent.run(config_path=args.config, n=args.n, model=args.model, out_dir=args.out_dir)
        res2 = risk_agent.run(config_path=args.config, out_dir=args.out_dir, group_by=args.group_by)
        print(json.dumps({"sas": res1, "risk": res2}, indent=2))

if __name__ == "__main__":
    main()
