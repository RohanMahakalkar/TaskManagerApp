SHELL := /bin/bash

.PHONY: install run test lint clean

install:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

run:
	./start.sh

test:
	cd $(CURDIR) && PYTHONPATH=. ./venv/bin/pytest -q

lint:
	# add lint commands (black, flake8) if desired
	@echo "No lint commands configured"

clean:
	@echo "Cleaning caches ..."
	rm -rf .pytest_cache __pycache__
