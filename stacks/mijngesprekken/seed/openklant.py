import os
from django.contrib.auth import get_user_model
from openklant.components.token.models import TokenAuth
from openklant.components.klantinteracties.models import Actor
U = get_user_model()
if not U.objects.filter(username="admin").exists():
    U.objects.create_superuser("admin", "admin@demogemeente.local", os.environ["DJANGO_SUPERUSER_PASSWORD"])
TokenAuth.objects.update_or_create(identifier="mgdemo", defaults=dict(token=os.environ["OK_TOKEN"], contact_person="Beheer",
    email="beheer@demogemeente.local", organization="Demogemeente", application="MijnGesprekken-demo", administration="Demo"))
def actor(naam, soort="organisatorische_eenheid"):
    a = Actor.objects.filter(naam=naam).first()
    if not a:
        a = Actor.objects.create(naam=naam, soort_actor=soort, indicatie_actief=True)
    return a
mw = actor("Team Vergunningen")
auto = actor("Demogemeente (automatisch)", "geautomatiseerde_actor")
print("ACTOR", mw.uuid); print("AUTO", auto.uuid)
