# Zet Mijn profiel en Mijn aanvragen onder de homepage, zodat het OIP-menu (show_menu_below_id "home") ze toont.
from cms.models import Page
from django.db import transaction
home = Page.objects.get(reverse_id="home")
for p in Page.objects.exclude(pk=home.pk).filter(parent__isnull=True):
    with transaction.atomic():
        p.move_page(home, position="last-child")
    print("verplaatst", p.pk)
from cms.models import PageUrl
for u in PageUrl.objects.all(): print(u.page_id, u.path)
