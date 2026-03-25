import time
import sys
import json
import ollama
from pathlib import Path


class AIAssistant:
    def __init__(self, prompt_path="data/PROMPT.md", schema_path="data/schema.yaml"):
        self.prompt_path = Path(prompt_path)
        self.schema_path = Path(schema_path)

    def analyze_job(self, jd_path: Path, db_json_content: str):
        if not jd_path.exists():
            raise FileNotFoundError(f"Job Description not found at {jd_path}")
        output_json = jd_path.with_name(f"{jd_path.stem}.json")

        # Load context files
        jd_text = jd_path.read_text()
        system_instructions = self.prompt_path.read_text()
        schema_context = (
            self.schema_path.read_text()
            if self.schema_path.exists()
            else "Schema not found."
        )

        # Construct the prompt
        user_message = (
            f"SCHEMA CONTEXT:\n{schema_context}\n\n"
            f"DATABASE CONTENT (JSON):\n{db_json_content}\n\n"
            f"TARGET JOB DESCRIPTION:\n{jd_text}"
        )
        # model_name = "qwen2.5-coder:32b"
        model_name = "qwen3-coder:480b-cloud"
        print(f"── Context loaded for model: {model_name}")

        try:
            start_time = time.perf_counter()
            # Calling Ollama with format='json' ensures the model attempts a JSON-ready string
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_message},
                ],
                format="json",
                options={
                    "temperature": 0,  # Make it less "creative" and more literal
                    # "num_predict": 1024,  # Ensure it doesn't cut off
                },
            )

            plan = json.loads(response["message"]["content"])

            end_time = time.perf_counter()
            duration = end_time - start_time
            print(f"── AI Analysis complete in {duration:.2f} seconds")

            total_duration_raw = response.get("total_duration")
            load_duration_raw = response.get("load_duration")
            eval_duration_raw = response.get("eval_duration")
            eval_count = response.get("eval_count") or 0

            total_duration = (total_duration_raw / 1e9) if total_duration_raw else 0
            load_duration = (load_duration_raw / 1e9) if load_duration_raw else 0
            eval_duration = (eval_duration_raw / 1e9) if eval_duration_raw else 0

            tokens_per_sec = eval_count / eval_duration if eval_duration > 0 else 0

            if eval_duration > 0:
                print(
                    f"── Total: {total_duration:.2f}s | Load: {load_duration:.2f}s | Gen: {eval_duration:.2f}s"
                )
                print(f"── Speed: {tokens_per_sec:.2f} tokens/sec")
            else:
                print(
                    "── Stats: Remote/Cloud model did not provide detailed timing metadata."
                )

            print(f"── Dumping json ouptut to: {str(output_json)}")
            json_string = json.dumps(plan, indent=4)
            output_json.write_text(json_string, encoding="utf-8")

            return plan

        except Exception as e:
            print(f"✘ AI Analysis failed: {e}")
            # Fallback to a minimal structure to prevent script crash if needed
            sys.exit(1)
