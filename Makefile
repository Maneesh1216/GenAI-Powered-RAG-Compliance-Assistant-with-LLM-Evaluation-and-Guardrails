.PHONY: install install-full index ask eval test api ui docker clean

install:       ## minimal install — runs with numpy only
	pip install -r requirements.txt

install-full:  ## transformers, FAISS, FastAPI, Streamlit, MLflow
	pip install -r requirements-full.txt

index:         ## build the hybrid index from data/policies
	python scripts/build_index.py

ask:           ## make ask Q="how long are audit logs retained"
	python scripts/ask.py "$(Q)"

eval:          ## run the golden set and print metrics
	python scripts/run_eval.py

test:
	python -m pytest tests -q

api:
	uvicorn compliance_assistant.api:app --app-dir src --reload --port 8000

ui:
	streamlit run app/streamlit_app.py

docker:
	docker build -t compliance-assistant .

clean:
	rm -rf .index runs.jsonl eval/results .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
