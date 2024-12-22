compose:
	docker compose up -d
db-shell:
	docker compose exec db psql -U test_user -d test_database
