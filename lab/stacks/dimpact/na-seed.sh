# Na de seed (gesourcet door scripts/stack.sh seed dimpact; de functie compose bestaat).
# Open Archiefbeheer haalt afgesloten zaken uit Open Zaak normaal 's nachts op (celery
# beat, 00:00). Voor de demo direct, zodat de vernietigingslijsten meteen zaken tonen.
compose exec -T openarchiefbeheer python src/manage.py cache_zaken
