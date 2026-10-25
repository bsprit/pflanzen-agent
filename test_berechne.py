"""Tests für berechne.py. Aufruf: python3 -m unittest test_berechne -v"""
import unittest
from datetime import datetime

from berechne import ZONE, verarbeite


def um(tag, stunde=8):
    return datetime.fromisoformat(f"{tag}T{stunde:02d}:00").replace(tzinfo=ZONE)


def antwort(text, tag, stunde=9):
    return {"event": "message", "time": int(um(tag, stunde).timestamp()), "message": text}


def daten(zuletzt="2026-11-01", naechstes="2026-11-13"):
    return {
        "jahreszeiten": {"sommer": [4, 5, 6, 7, 8, 9], "uebergang": [3, 10], "winter": [11, 12, 1, 2]},
        "pflanzen": [{
            "id": "pilea", "name": "Ufopflanze", "emoji": "🪴", "kurztipp": "Fingerprobe.",
            "intervallTage": {"sommer": 7, "uebergang": 10, "winter": 12},
            "zuletztGegossen": zuletzt, "zuletztGegossenQuelle": "angenommen",
            "naechstesGiessen": naechstes, "heuteFaellig": None, "verlauf": [],
        }],
    }


class Tests(unittest.TestCase):
    def test_version1_daten_werden_uebernommen(self):
        d = daten()
        verarbeite(d, [], um("2026-11-05", 14), morgens=False)
        p = d["pflanzen"][0]
        self.assertNotIn("heuteFaellig", p)
        self.assertIsNone(p["offen"])
        self.assertEqual(p["naechstesGiessen"], "2026-11-13")  # Winter: 12 Tage

    def test_faellig_morgens_erinnert(self):
        d = daten()
        erinnern = verarbeite(d, [], um("2026-11-13"), morgens=True)
        self.assertEqual([p["id"] for p in erinnern], ["pilea"])
        self.assertEqual(d["pflanzen"][0]["offen"]["erinnerungen"], 1)

    def test_nicht_faellig_kein_push(self):
        d = daten()
        self.assertEqual(verarbeite(d, [], um("2026-11-12"), morgens=True), [])

    def test_zwischenlauf_erinnert_nicht(self):
        d = daten()
        self.assertEqual(verarbeite(d, [], um("2026-11-13", 14), morgens=False), [])
        self.assertIsNone(d["pflanzen"][0]["offen"])

    def test_zweiter_lauf_am_selben_morgen_kein_doppelter_push(self):
        d = daten()
        verarbeite(d, [], um("2026-11-13"), morgens=True)
        self.assertEqual(verarbeite(d, [], um("2026-11-13", 9), morgens=True), [])

    def test_gegossen_knopf(self):
        d = daten()
        verarbeite(d, [], um("2026-11-13"), morgens=True)
        verarbeite(d, [antwort("gegossen:pilea", "2026-11-13")], um("2026-11-13", 14), morgens=False)
        p = d["pflanzen"][0]
        self.assertIsNone(p["offen"])
        self.assertEqual(p["zuletztGegossen"], "2026-11-13")
        self.assertEqual(p["zuletztGegossenQuelle"], "bestaetigt")
        self.assertEqual(p["naechstesGiessen"], "2026-11-25")

    def test_noch_feucht_verschiebt_im_winter_um_4_tage_und_lernt(self):
        d = daten()
        verarbeite(d, [], um("2026-11-13"), morgens=True)
        verarbeite(d, [antwort("feucht:pilea", "2026-11-13")], um("2026-11-13", 14), morgens=False)
        p = d["pflanzen"][0]
        self.assertIsNone(p["offen"])
        self.assertEqual(p["naechstesGiessen"], "2026-11-17")
        self.assertEqual(p["intervallTage"]["winter"], 13)
        self.assertEqual(verarbeite(d, [], um("2026-11-16"), morgens=True), [])
        self.assertEqual(len(verarbeite(d, [], um("2026-11-17"), morgens=True)), 1)
        self.assertEqual(p["offen"]["erinnerungen"], 1)
        # Danach gilt der gelernte Abstand.
        verarbeite(d, [antwort("gegossen:pilea", "2026-11-17")], um("2026-11-17", 14), morgens=False)
        self.assertEqual(p["naechstesGiessen"], "2026-11-30")

    def test_noch_feucht_im_sommer_2_tage(self):
        d = daten(zuletzt="2026-06-01", naechstes="2026-06-08")
        verarbeite(d, [antwort("feucht:pilea", "2026-06-08")], um("2026-06-08", 14), morgens=False)
        p = d["pflanzen"][0]
        self.assertEqual(p["naechstesGiessen"], "2026-06-10")
        self.assertEqual(p["intervallTage"]["sommer"], 8)
        self.assertEqual(p["intervallTage"]["winter"], 12)

    def test_gelernter_abstand_hat_obergrenze(self):
        d = daten()
        d["pflanzen"][0]["intervallTage"]["winter"] = 30
        verarbeite(d, [antwort("feucht:pilea", "2026-11-13")], um("2026-11-13", 14), morgens=False)
        self.assertEqual(d["pflanzen"][0]["intervallTage"]["winter"], 30)

    def test_ohne_antwort_zweite_erinnerung_dann_angenommen(self):
        d = daten()
        p = d["pflanzen"][0]
        verarbeite(d, [], um("2026-11-13"), morgens=True)
        self.assertEqual(len(verarbeite(d, [], um("2026-11-14"), morgens=True)), 1)
        self.assertEqual(p["offen"]["erinnerungen"], 2)
        self.assertEqual(verarbeite(d, [], um("2026-11-15"), morgens=True), [])
        self.assertIsNone(p["offen"])
        self.assertEqual(p["zuletztGegossen"], "2026-11-14")
        self.assertEqual(p["zuletztGegossenQuelle"], "angenommen")
        self.assertEqual(p["naechstesGiessen"], "2026-11-26")

    def test_gegossen_ohne_erinnerung(self):
        d = daten()
        verarbeite(d, [antwort("gegossen:pilea", "2026-11-08")], um("2026-11-08", 14), morgens=False)
        self.assertEqual(d["pflanzen"][0]["naechstesGiessen"], "2026-11-20")

    def test_alte_antwort_wird_nicht_doppelt_verarbeitet(self):
        d = daten()
        a = antwort("gegossen:pilea", "2026-11-08")
        verarbeite(d, [a], um("2026-11-08", 14), morgens=False)
        verarbeite(d, [], um("2026-11-20"), morgens=True)  # erinnert
        verarbeite(d, [a], um("2026-11-20", 14), morgens=False)
        self.assertIsNotNone(d["pflanzen"][0]["offen"])

    def test_unbekannte_antwort_wird_ignoriert(self):
        d = daten()
        verarbeite(d, [antwort("hallo", "2026-11-08"), antwort("gegossen:kaktus", "2026-11-08")],
                   um("2026-11-08", 14), morgens=False)
        self.assertEqual(d["pflanzen"][0]["zuletztGegossen"], "2026-11-01")


if __name__ == "__main__":
    unittest.main()
