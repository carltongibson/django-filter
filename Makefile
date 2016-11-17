.PHONY: deps, test

deps:
	pip install -r ./requirements/test.txt

test:
	./runtests.py