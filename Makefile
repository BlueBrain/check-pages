venv:
	if python -m ensurepip --version; then python -m venv $@; else virtualenv $@; fi
	venv/bin/pip install --upgrade pip
	venv/bin/pip install pycodestyle pylint

lint: | venv
	venv/bin/pycodestyle --max-line-length=100 -- *.py
	venv/bin/pylint -d E1120,E0401,R0912,R0913,R0914 *.py
