"""Fictieve testdata voor Gemeente Voorbeeldstad.

Alle personen zijn RvIG-testpersonen met een BSN in de officiele testreeks
(999990000-999999999, elfproef). Medewerkers, kentekens, e-mailadressen en
telefoonnummers zijn verzonnen. Het telefoonnummerblok 06-12345xxx en het
domein .example zijn bedoeld voor voorbeelden.
"""

SELECTIELIJST = "http://selectielijst.local:8000/api/v1"


def sl_procestype(uuid):
    return f"{SELECTIELIJST}/procestypen/{uuid}"


def sl_resultaat(uuid):
    return f"{SELECTIELIJST}/resultaten/{uuid}"


# Generieke resultaattypeomschrijvingen (config/selectielijst/resultaattypeomschrijvingen.json)
RESULTAATTYPEOMSCHRIJVINGEN = {
    "Toegekend": "fb65d251-1518-4185-865f-b8bdcfad07b1",
    "Afgewezen": "e6a0c939-3404-45b0-88e3-76c94fb80ea7",
    "Geweigerd": "1f750958-431c-4916-bc01-af5d3a753b41",
    "Verleend": "f7d2dc14-1b71-4179-aed3-4e7abcfbeb0d",
    "Afgehandeld": "7cb315fb-4f7b-4a43-aca1-e4522e4c73b3",
    "Niet nodig": "3c23a936-ab4b-4715-a05b-b122d62ff050",
}


def sl_rto(naam):
    return f"{SELECTIELIJST}/resultaattypeomschrijvingen/{RESULTAATTYPEOMSCHRIJVINGEN[naam]}"


CATALOGUS = {
    "domein": "VBSTD",
    "naam": "Zaaktypecatalogus Gemeente Voorbeeldstad",
    "versie": "2026.1",
    "begindatumVersie": "2026-01-01",
    "contactpersoonBeheerNaam": "Team Informatiebeheer",
    "contactpersoonBeheerEmailadres": "informatiebeheer@voorbeeldstad.example",
    "contactpersoonBeheerTelefoonnummer": "0612345000",
}

# Informatieobjecttypen (documentsoorten), gedeeld door de zaaktypen
INFORMATIEOBJECTTYPEN = {
    "aanvraag": {"omschrijving": "Aanvraagformulier", "informatieobjectcategorie": "Aanvraag", "vertrouwelijkheidaanduiding": "zaakvertrouwelijk"},
    "bijlage": {"omschrijving": "Bijlage bij aanvraag", "informatieobjectcategorie": "Bijlage", "vertrouwelijkheidaanduiding": "zaakvertrouwelijk"},
    "melding": {"omschrijving": "Melding", "informatieobjectcategorie": "Melding", "vertrouwelijkheidaanduiding": "openbaar"},
    "foto": {"omschrijving": "Foto", "informatieobjectcategorie": "Foto", "vertrouwelijkheidaanduiding": "openbaar"},
    "besluit": {"omschrijving": "Besluitbrief", "informatieobjectcategorie": "Besluit", "vertrouwelijkheidaanduiding": "zaakvertrouwelijk"},
    "verslag": {"omschrijving": "Gespreksverslag", "informatieobjectcategorie": "Verslag", "vertrouwelijkheidaanduiding": "vertrouwelijk"},
}

ZAAKTYPEN = [
    {
        "sleutel": "omgevingsvergunning",
        "identificatie": "VBS-OMGVERG",
        "omschrijving": "Omgevingsvergunning aanvragen",
        "omschrijvingGeneriek": "Omgevingsvergunning",
        "doel": "Beoordelen of een activiteit in de fysieke leefomgeving (bouwen, kappen, verbouwen) toegestaan is.",
        "aanleiding": "Een inwoner of bedrijf dient een aanvraag omgevingsvergunning in.",
        "onderwerp": "Omgevingsvergunning",
        "handelingInitiator": "Aanvragen",
        "handelingBehandelaar": "Behandelen",
        "doorlooptijd": "P56D",
        "servicenorm": "P42D",
        "opschortingEnAanhoudingMogelijk": True,
        "verlengingMogelijk": True,
        "verlengingstermijn": "P42D",
        "vertrouwelijkheidaanduiding": "zaakvertrouwelijk",
        "trefwoorden": ["omgevingswet", "vergunning", "bouwen"],
        "productenOfDiensten": ["http://standaarden.overheid.nl/owms/terms/Omgevingsvergunning"],
        "referentieproces": {"naam": "Vergunning verlenen"},
        "selectielijstProcestype": sl_procestype("3e1f6d3e-617f-43e1-87be-8bd255ef4745"),  # 11 Toestemming verlenen
        "statustypen": [
            ("Ontvangen", "Wij hebben uw aanvraag ontvangen."),
            ("In behandeling", "Wij beoordelen uw aanvraag."),
            ("Besluit genomen", "Er is een besluit genomen over uw aanvraag."),
        ],
        "resultaattypen": [
            ("Verleend", "de0cade3-a070-4ae0-9ba6-41256c4bc0f8", "blijvend_bewaren", "Verleend"),
            ("Geweigerd", "bcd33d3a-4a34-4143-9569-4d161ea6da6b", "vernietigen", "Geweigerd"),
        ],
        "documenten": [("aanvraag", "inkomend"), ("bijlage", "inkomend"), ("besluit", "uitgaand")],
    },
    {
        "sleutel": "mor",
        "identificatie": "VBS-MOR",
        "omschrijving": "Melding openbare ruimte",
        "omschrijvingGeneriek": "Melding openbare ruimte",
        "doel": "Meldingen over de openbare ruimte (afval, bestrating, verlichting, groen) afhandelen.",
        "aanleiding": "Een inwoner doet een melding over de openbare ruimte.",
        "onderwerp": "Openbare ruimte",
        "handelingInitiator": "Melden",
        "handelingBehandelaar": "Afhandelen",
        "doorlooptijd": "P14D",
        "servicenorm": "P5D",
        "opschortingEnAanhoudingMogelijk": False,
        "verlengingMogelijk": False,
        "vertrouwelijkheidaanduiding": "openbaar",
        "trefwoorden": ["melding", "openbare ruimte", "MOR"],
        "productenOfDiensten": ["http://standaarden.overheid.nl/owms/terms/Melding_openbare_ruimte"],
        "referentieproces": {"naam": "Onderhouden en repareren"},
        "selectielijstProcestype": sl_procestype("388645ae-bb7f-4b2b-ba70-94b70f713d45"),  # 15 Onderhouden en repareren
        "statustypen": [
            ("Ontvangen", "Wij hebben uw melding ontvangen."),
            ("Ingepland", "Uw melding is ingepland bij de buitendienst."),
            ("Afgehandeld", "Uw melding is afgehandeld."),
        ],
        "resultaattypen": [
            ("Uitgevoerd", "d8b21822-3ff1-4414-b17b-cbfd662b40d8", "vernietigen", "Afgehandeld"),
            ("Niet uitgevoerd", "b8a84964-7cb1-4294-9fbf-edc4251f538b", "vernietigen", "Niet nodig"),
        ],
        "documenten": [("melding", "inkomend"), ("foto", "inkomend")],
    },
    {
        "sleutel": "wmo",
        "identificatie": "VBS-WMO",
        "omschrijving": "Wmo-maatwerkvoorziening aanvragen",
        "omschrijvingGeneriek": "Wmo-aanvraag",
        "doel": "Vaststellen of een inwoner recht heeft op een maatwerkvoorziening op grond van de Wmo 2015.",
        "aanleiding": "Een inwoner vraagt ondersteuning aan (bijvoorbeeld huishoudelijke hulp of een traplift).",
        "onderwerp": "Wmo-maatwerkvoorziening",
        "handelingInitiator": "Aanvragen",
        "handelingBehandelaar": "Beoordelen",
        "doorlooptijd": "P56D",
        "servicenorm": "P42D",
        "opschortingEnAanhoudingMogelijk": True,
        "verlengingMogelijk": True,
        "verlengingstermijn": "P14D",
        "vertrouwelijkheidaanduiding": "vertrouwelijk",
        "trefwoorden": ["wmo", "zorg", "ondersteuning"],
        "productenOfDiensten": ["http://standaarden.overheid.nl/owms/terms/Wmo-maatwerkvoorziening"],
        "referentieproces": {"naam": "Voorzieningen verstrekken"},
        "selectielijstProcestype": sl_procestype("bd1ec0a0-0ecd-4046-8372-dcb6bdfda891"),  # 8 Voorzieningen verstrekken
        "statustypen": [
            ("Ontvangen", "Wij hebben uw aanvraag ontvangen."),
            ("Gesprek gepland", "Wij nemen contact met u op voor een keukentafelgesprek."),
            ("In behandeling", "Wij beoordelen uw aanvraag."),
            ("Besluit genomen", "Er is een besluit genomen over uw aanvraag."),
        ],
        "resultaattypen": [
            ("Verstrekt", "d97defa2-764f-402c-b3d7-b8db60ae340b", "vernietigen", "Toegekend"),
            ("Geweigerd", "e2068367-1012-4795-984e-72901180ff80", "vernietigen", "Geweigerd"),
        ],
        "documenten": [("aanvraag", "inkomend"), ("verslag", "intern"), ("besluit", "uitgaand")],
    },
    {
        "sleutel": "parkeervergunning",
        "identificatie": "VBS-PARKVERG",
        "omschrijving": "Parkeervergunning bewoners aanvragen",
        "omschrijvingGeneriek": "Parkeervergunning",
        "doel": "Een parkeervergunning voor bewoners van een betaald-parkerengebied verstrekken.",
        "aanleiding": "Een bewoner vraagt een parkeervergunning aan.",
        "onderwerp": "Parkeervergunning",
        "handelingInitiator": "Aanvragen",
        "handelingBehandelaar": "Behandelen",
        "doorlooptijd": "P28D",
        "servicenorm": "P5D",
        "opschortingEnAanhoudingMogelijk": False,
        "verlengingMogelijk": False,
        "vertrouwelijkheidaanduiding": "zaakvertrouwelijk",
        "trefwoorden": ["parkeren", "vergunning"],
        "productenOfDiensten": ["http://standaarden.overheid.nl/owms/terms/Parkeervergunning"],
        "referentieproces": {"naam": "Producten en diensten leveren"},
        "selectielijstProcestype": sl_procestype("651a1b5b-f84f-4c73-9151-4d485c7dcb99"),  # 5 Producten en diensten leveren
        "statustypen": [
            ("Ontvangen", "Wij hebben uw aanvraag ontvangen."),
            ("In behandeling", "Wij behandelen uw aanvraag."),
            ("Afgehandeld", "Uw aanvraag is afgehandeld."),
        ],
        "resultaattypen": [
            ("Geleverd", "ceb821a2-3b5e-421a-ac49-ebc63d15dc29", "vernietigen", "Toegekend"),
            ("Niet geleverd", "423c22eb-1237-4a8b-846d-1cb0a02d74b2", "vernietigen", "Afgewezen"),
        ],
        "documenten": [("aanvraag", "inkomend"), ("besluit", "uitgaand")],
    },
]

ROLTYPEN = [
    ("Aanvrager", "initiator"),
    ("Behandelaar", "behandelaar"),
]

# Fictieve medewerkers van Gemeente Voorbeeldstad
MEDEWERKERS = {
    "vergunningen": {"identificatie": "mdw-0101", "achternaam": "Vermeulen", "voorletters": "A.", "voorvoegselAchternaam": ""},
    "buitendienst": {"identificatie": "mdw-0202", "achternaam": "Bakker", "voorletters": "S.", "voorvoegselAchternaam": ""},
    "wmo": {"identificatie": "mdw-0303", "achternaam": "Dijk", "voorletters": "R.", "voorvoegselAchternaam": "van"},
    "parkeren": {"identificatie": "mdw-0404", "achternaam": "Smits", "voorletters": "L.", "voorvoegselAchternaam": ""},
}

# Test-inwoners (RvIG-testpersonen; naam en adres komen uit de BRP-mock)
INWONERS = ["999990627", "999997609", "999993409", "999995406", "999991991"]

# resultaattypen: (omschrijving, selectielijst-resultaat, archiefnominatie, generieke omschrijving)

# Zaken. "statussen" = aantal doorlopen statustypen (de laatste is de huidige).
# Een zaak met "resultaat" wordt afgesloten met de eindstatus.
ZAKEN = [
    {
        "identificatie": "VBS-2026-000101", "zaaktype": "omgevingsvergunning", "bsn": "999990627",
        "omschrijving": "Plaatsen dakkapel achterzijde woning",
        "toelichting": "Aanvraag voor een dakkapel van 3 meter breed aan de achterzijde.",
        "startdatum": "2026-08-18", "statussen": ["2026-08-18", "2026-08-25"], "behandelaar": "vergunningen",
        "documenten": [("aanvraag", "Aanvraag omgevingsvergunning dakkapel"), ("bijlage", "Bouwtekening dakkapel")],
    },
    {
        "identificatie": "VBS-2026-000102", "zaaktype": "mor", "bsn": "999990627",
        "omschrijving": "Losliggende trottoirtegels Mandelaplein",
        "toelichting": "Meerdere trottoirtegels liggen los, struikelgevaar.",
        "startdatum": "2026-09-02", "statussen": ["2026-09-02", "2026-09-04", "2026-09-09"], "behandelaar": "buitendienst",
        "resultaat": "Uitgevoerd", "melding": {"categorie": "Bestrating", "lat": 52.0699, "lon": 4.3006},
        "documenten": [("melding", "Melding losliggende trottoirtegels"), ("foto", "Foto trottoirtegels")],
    },
    {
        "identificatie": "VBS-2026-000103", "zaaktype": "parkeervergunning", "bsn": "999997609",
        "omschrijving": "Parkeervergunning bewoners zone Loosduinen",
        "toelichting": "Eerste vergunning voor het huishouden.",
        "startdatum": "2026-07-01", "statussen": ["2026-07-01", "2026-07-02", "2026-07-06"], "behandelaar": "parkeren",
        "resultaat": "Geleverd", "parkeervergunning": {"kenteken": "XX-999-X", "zone": "Loosduinen", "geldigVan": "2026-07-06", "geldigTot": "2027-07-05"},
        "documenten": [("aanvraag", "Aanvraag parkeervergunning"), ("besluit", "Besluit parkeervergunning")],
    },
    {
        "identificatie": "VBS-2026-000104", "zaaktype": "wmo", "bsn": "999997609",
        "omschrijving": "Aanvraag traplift",
        "toelichting": "Inwoner kan de trap niet meer veilig op.",
        "startdatum": "2026-09-15", "statussen": ["2026-09-15", "2026-09-22"], "behandelaar": "wmo",
        "documenten": [("aanvraag", "Aanvraag Wmo-voorziening traplift")],
    },
    {
        "identificatie": "VBS-2026-000105", "zaaktype": "wmo", "bsn": "999993409",
        "omschrijving": "Huishoudelijke ondersteuning",
        "toelichting": "Ondersteuning bij het schoonhouden van de woning.",
        "startdatum": "2026-06-03", "statussen": ["2026-06-03", "2026-06-10", "2026-06-17", "2026-07-08"], "behandelaar": "wmo",
        "resultaat": "Verstrekt",
        "documenten": [("aanvraag", "Aanvraag huishoudelijke ondersteuning"), ("verslag", "Verslag keukentafelgesprek"), ("besluit", "Beschikking huishoudelijke ondersteuning")],
    },
    {
        "identificatie": "VBS-2026-000106", "zaaktype": "mor", "bsn": "999995406",
        "omschrijving": "Zwerfafval bij ondergrondse container",
        "toelichting": "Vuilniszakken naast de container aan de Binckhorstlaan.",
        "startdatum": "2026-10-05", "statussen": ["2026-10-05"], "behandelaar": "buitendienst",
        "melding": {"categorie": "Afval", "lat": 52.0788, "lon": 4.3368},
        "documenten": [("melding", "Melding zwerfafval")],
    },
    {
        "identificatie": "VBS-2026-000107", "zaaktype": "parkeervergunning", "bsn": "999991991",
        "omschrijving": "Parkeervergunning bewoners zone Centrum",
        "toelichting": "Verhuisd naar het centrum.",
        "startdatum": "2026-10-01", "statussen": ["2026-10-01", "2026-10-02"], "behandelaar": "parkeren",
        "documenten": [("aanvraag", "Aanvraag parkeervergunning")],
    },
    {
        "identificatie": "VBS-2026-000108", "zaaktype": "omgevingsvergunning", "bsn": "999991991",
        "omschrijving": "Kappen boom in voortuin",
        "toelichting": "Verzoek tot het kappen van een gezonde lindeboom.",
        "startdatum": "2026-05-11", "statussen": ["2026-05-11", "2026-05-18", "2026-06-29"], "behandelaar": "vergunningen",
        "resultaat": "Geweigerd",
        "documenten": [("aanvraag", "Aanvraag omgevingsvergunning kappen"), ("besluit", "Besluit weigering kapvergunning")],
    },
]

# Contactmomenten in Open Klant (kanaalcodes uit Referentielijsten, tabel KANAAL)
KLANTCONTACTEN = [
    {"bsn": "999990627", "kanaal": "telefoon", "onderwerp": "Vraag over status aanvraag dakkapel", "inhoud": "Inwoner vraagt wanneer het besluit komt. Uitgelegd dat de beslistermijn 8 weken is.", "plaatsgevondenOp": "2026-09-01T10:15:00+02:00", "zaak": "VBS-2026-000101"},
    {"bsn": "999997609", "kanaal": "balie", "onderwerp": "Aanvraag traplift", "inhoud": "Inwoner heeft het aanvraagformulier ingeleverd aan de balie.", "plaatsgevondenOp": "2026-09-15T14:30:00+02:00", "zaak": "VBS-2026-000104"},
    {"bsn": "999993409", "kanaal": "email", "onderwerp": "Wijziging dagen huishoudelijke hulp", "inhoud": "Verzoek om de hulp op dinsdag in plaats van maandag te laten komen.", "plaatsgevondenOp": "2026-08-20T09:00:00+02:00", "zaak": "VBS-2026-000105"},
    {"bsn": "999995406", "kanaal": "webformulier", "onderwerp": "Melding zwerfafval", "inhoud": "Melding via het webformulier, zaak aangemaakt.", "plaatsgevondenOp": "2026-10-05T08:45:00+02:00", "zaak": "VBS-2026-000106"},
    {"bsn": "999991991", "kanaal": "telefoon", "onderwerp": "Bezwaar mogelijk tegen weigering kapvergunning?", "inhoud": "Uitgelegd hoe bezwaar gemaakt kan worden binnen 6 weken.", "plaatsgevondenOp": "2026-07-02T11:20:00+02:00", "zaak": "VBS-2026-000108"},
]

# Objecttypen in Open Object (UUID's staan ook in config/openobject/data.yaml)
OBJECTTYPEN = {
    "melding": {
        "uuid": "7c1d4a0e-5a7b-4c1e-8f00-0000000000a1",
        "naam": "Melding openbare ruimte",
        "schema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Melding openbare ruimte",
            "type": "object",
            "required": ["kenmerk", "categorie", "omschrijving", "locatie"],
            "properties": {
                "kenmerk": {"type": "string"},
                "categorie": {"type": "string", "enum": ["Afval", "Bestrating", "Groen", "Verlichting", "Overig"]},
                "omschrijving": {"type": "string"},
                "locatie": {"type": "object", "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}}},
                "melderBsn": {"type": "string", "pattern": "^[0-9]{9}$"},
                "zaak": {"type": "string", "format": "uri"},
            },
        },
    },
    "parkeervergunning": {
        "uuid": "7c1d4a0e-5a7b-4c1e-8f00-0000000000a2",
        "naam": "Parkeervergunning",
        "schema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Parkeervergunning",
            "type": "object",
            "required": ["kenmerk", "bsn", "kenteken", "zone", "geldigVan", "geldigTot"],
            "properties": {
                "kenmerk": {"type": "string"},
                "bsn": {"type": "string", "pattern": "^[0-9]{9}$"},
                "kenteken": {"type": "string"},
                "zone": {"type": "string"},
                "geldigVan": {"type": "string", "format": "date"},
                "geldigTot": {"type": "string", "format": "date"},
                "zaak": {"type": "string", "format": "uri"},
            },
        },
    },
}

# Open Product: thema en producttype met verwijzing naar de UPL
PRODUCT_THEMA = {"naam": "Parkeren", "beschrijving": "Vergunningen en ontheffingen voor parkeren in Voorbeeldstad."}
PRODUCTTYPE = {
    "code": "VBS-PARKVERG-BEWONER",
    "naam": "Parkeervergunning voor bewoners",
    "samenvatting": "Met een bewonersvergunning parkeert u in uw eigen parkeerzone.",
    "beschrijving": "Woont u in een gebied met betaald parkeren? Dan kunt u een parkeervergunning voor bewoners aanvragen.",
    "upl_naam": "parkeervergunning",
}
