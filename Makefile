.DEFAULT_GOAL := help
BIN := ./bin/daimon

.PHONY: help install install-load doctor sync validate status tui test

help:
	@echo "dAImon — make targets:"
	@echo "  make install        install hooks, TUI venv, skills, plists (not scheduled)"
	@echo "  make install-load   install and load the launchd jobs (schedules them)"
	@echo "  make doctor         preflight checks (tools, auth, hooks, config)"
	@echo "  make sync           regenerate plists + skills from config"
	@echo "  make validate       validate configuration"
	@echo "  make status         show launchd + running-session state"
	@echo "  make tui            open the control panel"
	@echo "  make test           run the test suite"

install:
	@$(BIN) install

install-load:
	@$(BIN) install --load

doctor:
	@$(BIN) doctor

sync:
	@$(BIN) sync

validate:
	@$(BIN) validate

status:
	@$(BIN) status

tui:
	@$(BIN) tui

test:
	@bash tests/run.sh
