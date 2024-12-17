compose:
	docker compose up -d
db-shell:
	psql -U test_user -h localhost -p 5433 -d test_database
