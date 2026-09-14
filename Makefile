.PHONY: help init test up stop logs upgrade static
help:
	@bash scripts/dev.sh help
init:
	bash scripts/dev.sh init
up:
	bash scripts/dev.sh up
stop:
	bash scripts/dev.sh stop
logs:
	bash scripts/dev.sh logs
test:
	bash scripts/dev.sh test
upgrade:
	bash scripts/dev.sh upgrade
static:
	python3 scripts/static_check.py
