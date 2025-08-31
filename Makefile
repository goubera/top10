venv:
	python -m venv .venv && echo "Run 'source .venv/bin/activate'"

install:
	pip install -r solana-meme-top10-collector/requirements.txt

run:
	python solana-meme-top10-collector/collector.py

test:
	pytest -q
