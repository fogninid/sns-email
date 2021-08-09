PYENV = .pyenv

.PHONY: all
all:
	@echo nothing to do

$(PYENV):
	@virtualenv $(PYENV)
	@$(PYENV)/bin/pip install -r requirements.txt
	@$(PYENV)/bin/pip install --use-feature=in-tree-build -e .

.PHONY: test
test: $(PYENV)
	@$(PYENV)/bin/pytest

.PHONY: coverage
coverage: $(PYENV)
	@$(PYENV)/bin/coverage run -m pytest
	@$(PYENV)/bin/coverage html
	@$(PYENV)/bin/coverage report
	@echo
	@echo file://$(PWD)/coverage_html_report/index.html

.PHONY: clean
clean:
	rm -rf -- $(PYENV)
