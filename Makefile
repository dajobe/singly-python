PYTHONS=singly.py

all:
	@echo "Nothing to do"

clean:
	rm -f *~ *pyc

lint:
	pylint-2.7 $(PYTHONS)
