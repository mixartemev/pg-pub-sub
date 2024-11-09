compose:
	docker compose up -d
db-shell:
	pgcli -U test_user -h localhost -d test_database
run:
	python3 src/main.py
