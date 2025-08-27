import subprocess, json

class OllamaCLI:
    """
    Minimal wrapper that calls `ollama generate` (no localhost HTTP).
    We ask the model to return strict JSON; we also stitch streaming JSON lines.
    """
    def __init__(self, model: str = "llama3.1:8b-instruct", temperature: float = 0.2, max_tokens: int = 1024):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_json(self, prompt: str) -> str:
        """
        Returns text output (string). Uses streaming --json and concatenates 'response' chunks.
        """
        cmd = [
            "ollama", "generate",
            "-m", self.model,
            "-p", prompt,
            "--json",
            "-o", f"temperature={self.temperature}",
            "-o", f"num_predict={self.max_tokens}"
        ]

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except FileNotFoundError:
            raise RuntimeError("Ollama CLI not found. Install with: curl -fsSL https://ollama.com/install.sh | sh")

        full_text = ""
        for line in proc.stdout:
            try:
                obj = json.loads(line)
                if "response" in obj:
                    full_text += obj["response"]
            except json.JSONDecodeError:
                continue
        _, err = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Ollama error: {err.strip()}")
        return full_text.strip()
