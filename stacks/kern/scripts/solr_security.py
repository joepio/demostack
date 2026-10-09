"""Print Solr security.json met basic auth voor gebruiker zac (hash volgens Solr: sha256(sha256(salt+wachtwoord)))."""
import base64, hashlib, json, os, sys
pw = os.environ["SOLR_PASSWORD"].encode()
salt = hashlib.sha256(b"demostack-solr-" + pw).digest()  # deterministisch, zodat het bestand stabiel blijft
h = base64.b64encode(hashlib.sha256(hashlib.sha256(salt + pw).digest()).digest()).decode() + " " + base64.b64encode(salt).decode()
json.dump({"authentication": {"class": "solr.BasicAuthPlugin", "blockUnknown": True, "realm": "ZAC Solr",
                              "forwardCredentials": False, "credentials": {"zac": h}},
           "authorization": {"class": "solr.RuleBasedAuthorizationPlugin",
                             "permissions": [{"name": "all", "role": "admin"}], "user-role": {"zac": "admin"}}},
          sys.stdout, indent=1)
