#!/usr/bin/env bash
# Test-PKI voor OpenFSC in stack vcg (alleen voor deze demo, niet in git:
# stacks/vcg/.fsc-pki/ staat in .gitignore). Idempotent: bestaat de PKI al, dan niets.
#
# FSC kent twee soorten certificaten:
#   groep (extern)  uitgegeven door de CA van de FSC-groep; het subject draagt de
#                   organisatie (O) en het peer-id (serialNumber, bij de overheid het OIN).
#                   Hier een eigen test-CA "FSC-testgroep Voorbeeldstad".
#   intern          per organisatie een eigen CA voor het verkeer tussen de eigen
#                   componenten (manager, controller, inway/outway, txlog) en beheer.
#
# Peers (fictief, testnummers):
#   directory          00000099000000000000  FSC-directory testgroep
#   voorbeeldstad      00000099000000000001  Gemeente Voorbeeldstad (afnemer, outway)
#   brp                00000099000000000002  BRP-leverancier Testland (aanbieder, inway)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PKI="${FSC_PKI_DIR:-$ROOT/stacks/vcg/.fsc-pki}"
# De FSC-images draaien als appuser (uid/gid 1001); sleutels mogen niet voor iedereen
# leesbaar zijn (OpenFSC controleert dat), dus 0640 met groep 1001
FSC_GID=1001

[ -s "$PKI/klaar" ] && exit 0
echo "==> test-PKI voor OpenFSC maken ($PKI)"
rm -rf "$PKI"; mkdir -p "$PKI"

ca() {  # ca <map> <naam>
    mkdir -p "$1"
    openssl req -x509 -newkey rsa:4096 -nodes -days 1095 -subj "/C=NL/O=Demogemeente Voorbeeldstad/CN=$2" \
        -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" \
        -keyout "$1/ca-key.pem" -out "$1/root.pem" 2>/dev/null
}

cert() {  # cert <ca-map> <doelmap> <subject> <dns,dns,...>
    local cadir="$1" dir="$2" subj="$3" san="" h
    mkdir -p "$dir"
    for h in ${4//,/ }; do san="${san:+$san,}DNS:$h"; done
    openssl req -newkey rsa:4096 -nodes -subj "$subj" -keyout "$dir/key.pem" -out "$dir/csr.pem" 2>/dev/null
    printf 'subjectAltName=%s\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth,clientAuth\nbasicConstraints=CA:FALSE\n' \
        "$san" > "$dir/ext.cnf"
    openssl x509 -req -in "$dir/csr.pem" -CA "$cadir/root.pem" -CAkey "$cadir/ca-key.pem" -CAcreateserial \
        -days 1095 -sha256 -extfile "$dir/ext.cnf" -out "$dir/cert.pem" 2>/dev/null
    rm -f "$dir/csr.pem" "$dir/ext.cnf"
}

# Groep (extern)
G="$PKI/groep"
ca "$G/ca" "FSC-testgroep Voorbeeldstad CA"
cert "$G/ca" "$G/directory" "/C=NL/O=FSC-directory testgroep/serialNumber=00000099000000000000/CN=directory.fsc.local" directory.fsc.local
cert "$G/ca" "$G/voorbeeldstad-manager" "/C=NL/O=Gemeente Voorbeeldstad/serialNumber=00000099000000000001/CN=manager.voorbeeldstad.fsc.local" manager.voorbeeldstad.fsc.local
cert "$G/ca" "$G/voorbeeldstad-outway" "/C=NL/O=Gemeente Voorbeeldstad/serialNumber=00000099000000000001/CN=outway.voorbeeldstad.fsc.local" outway.voorbeeldstad.fsc.local
cert "$G/ca" "$G/brp-manager" "/C=NL/O=BRP-leverancier Testland/serialNumber=00000099000000000002/CN=manager.brp.fsc.local" manager.brp.fsc.local
cert "$G/ca" "$G/brp-inway" "/C=NL/O=BRP-leverancier Testland/serialNumber=00000099000000000002/CN=inway.brp.fsc.local" inway.brp.fsc.local

# Intern per organisatie
for org in directory voorbeeldstad brp; do
    I="$PKI/intern/$org"
    ca "$I/ca" "FSC intern $org CA"
    onderdelen="manager controller beheer"
    case "$org" in
        voorbeeldstad) onderdelen="$onderdelen outway txlog" ;;
        brp) onderdelen="$onderdelen inway txlog" ;;
    esac
    for o in $onderdelen; do
        cert "$I/ca" "$I/$o" "/C=NL/O=$org/CN=$o.$org.fsc.local" "$o.$org.fsc.local"
    done
done
# Directory-manager is intern en extern bereikbaar onder directory.fsc.local
cert "$PKI/intern/directory/ca" "$PKI/intern/directory/manager" "/C=NL/O=directory/CN=directory.fsc.local" \
    "directory.fsc.local,manager.directory.fsc.local"

find "$PKI" -name '*.pem' -exec chmod 644 {} +
find "$PKI" -name 'key.pem' -exec chmod 640 {} + -exec chown "0:$FSC_GID" {} +
find "$PKI" -name 'ca-key.pem' -exec chmod 600 {} +
find "$PKI" -name '*.srl' -delete
date -u +%FT%TZ > "$PKI/klaar"
