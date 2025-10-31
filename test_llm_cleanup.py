#!/usr/bin/env python3
"""
Test per verificare che format_summary_text rimuova correttamente le introduzioni del LLM
e gestisca gli spazi eccessivi.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from utils import format_summary_text


def test_llm_intro_removal():
    """Test rimozione introduzioni comuni del LLM."""

    print("🧪 Test Rimozione Introduzioni LLM")
    print("=" * 70)

    test_cases = [
        {
            "name": "Certamente! Ecco...",
            "input": "Certamente!\n\nEcco un riassunto dell'articolo.\n\nIl contenuto principale è questo.",
            "should_start_with": "Il contenuto",
        },
        {
            "name": "Ecco a te il riassunto",
            "input": "Ecco a te il riassunto!\n\nIl testo importante inizia qui.",
            "should_start_with": "Il testo",
        },
        {
            "name": "Certo! Ecco...",
            "input": "Certo! Ecco il riassunto che hai richiesto.\n\nContenuto vero.",
            "should_start_with": "Contenuto",
        },
        {
            "name": "Va bene!",
            "input": "Va bene!\n\nQuesta è la parte importante.",
            "should_start_with": "Questa",
        },
        {
            "name": "Perfetto!",
            "input": "Perfetto!\n\nIl riassunto reale parte da qui.",
            "should_start_with": "Il riassunto",
        },
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        print(f"\n📝 Test: {test['name']}")
        print(f"   Input: {test['input'][:50]}...")

        result = format_summary_text(test["input"])

        print(f"   Output: {result[:50]}...")

        if result.startswith(test["should_start_with"]):
            print(f"   ✅ PASS - Inizia con '{test['should_start_with']}'")
            passed += 1
        else:
            print(f"   ❌ FAIL - Non inizia con '{test['should_start_with']}'")
            print(f"   Risultato: {result[:100]}")
            failed += 1

    print(f"\n📊 Risultato: {passed}/{len(test_cases)} test passati")
    return failed == 0


def test_excessive_spacing():
    """Test rimozione spazi eccessivi."""

    print("\n\n🧪 Test Rimozione Spazi Eccessivi")
    print("=" * 70)

    # Esempio reale dal bot
    real_example = """Certamente!


Ecco un riassunto dell'articolo in un singolo paragrafo.



💥 L'espulsione da un aereo militare.


Si tratta di una procedura incredibilmente violenta.


Tra le conseguenze più comuni vi è la compressione spinale."""

    print(f"\n📥 INPUT (con spazi eccessivi):")
    print("-" * 70)
    print(real_example)
    print("-" * 70)
    print(f"Lines: {len(real_example.split(chr(10)))}")

    result = format_summary_text(real_example)

    print(f"\n📤 OUTPUT (dopo pulizia):")
    print("-" * 70)
    print(result)
    print("-" * 70)
    print(f"Lines: {len(result.split(chr(10)))}")

    # Verifica che non ci siano più di 1 a capo consecutivo
    if "\n\n" in result:
        print("\n⚠️  WARNING: Ancora presenti doppi a capo")
        return False

    # Verifica che non inizi con "Certamente"
    if result.lower().startswith("certamente"):
        print("\n❌ FAIL: Inizia ancora con 'Certamente'")
        return False

    # Verifica che non inizi con "Ecco"
    if result.lower().startswith("ecco"):
        print("\n❌ FAIL: Inizia ancora con 'Ecco'")
        return False

    print("\n✅ PASS - Spazi eccessivi rimossi e introduzioni eliminate")
    return True


def test_abbreviations_preserved():
    """Test che le abbreviazioni siano ancora preservate dopo le modifiche."""

    print("\n\n🧪 Test Preservazione Abbreviazioni")
    print("=" * 70)

    test = (
        "Certamente! Il Dr. Smith e MJ. Jackson hanno lavorato per Apple Inc. nel 2024."
    )

    print(f"\n📥 INPUT: {test}")

    result = format_summary_text(test)

    print(f"📤 OUTPUT: {result}")

    issues = []
    if "Dr.\n" in result or " Dr.\n" in result:
        issues.append("❌ A capo dopo Dr.")
    if "MJ.\n" in result or " MJ.\n" in result:
        issues.append("❌ A capo dopo MJ.")
    if "Inc.\n" in result or " Inc.\n" in result:
        issues.append("❌ A capo dopo Inc.")
    if result.lower().startswith("certamente"):
        issues.append("❌ Inizia ancora con 'Certamente'")

    if issues:
        print("\n⚠️  PROBLEMI:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("\n✅ PASS - Abbreviazioni preservate e introduzione rimossa")
        return True


def test_real_world_example():
    """Test con l'esempio reale fornito dall'utente."""

    print("\n\n🧪 Test Esempio Reale Utente")
    print("=" * 70)

    real_input = """Certamente!


Ecco un riassunto dell'articolo in un singolo paragrafo, arricchito con formattazione Markdown ed emoji contestuali.



💥 L'espulsione da un aereo militare non è un'azione di routine, ma una misura estrema di ultima istanza 🚨.


Si tratta di una procedura incredibilmente violenta, con un impatto che può raggiungere i 20g, la quale quasi sempre provoca lesioni al pilota 🤕.


Tra le conseguenze più comuni vi è la compressione spinale 🦴, che spesso causa una perdita permanente di altezza.


Sebbene i moderni sistemi di espulsione abbiano un tasso di successo del 90-92% ✅, è fondamentale capire che per "successo" si intende unicamente la sopravvivenza del pilota, non l'assenza di danni fisici.


Pertanto, questa opzione viene scelta solo quando l'alternativa è la morte certa 💀 e il velivolo è già considerato incontrollabile 🌪️ o sta per diventarlo, rendendo irrilevante qualsiasi programmazione del pilota automatico."""

    print(f"\n📥 INPUT (esempio reale):")
    print("-" * 70)
    print(real_input[:200] + "...")
    print(f"\nTotal lines: {len(real_input.split(chr(10)))}")
    print(f"Empty lines: {real_input.count(chr(10)*2)}")

    result = format_summary_text(real_input)

    print(f"\n📤 OUTPUT (dopo format_summary_text):")
    print("-" * 70)
    print(result)
    print("-" * 70)
    print(f"\nTotal lines: {len(result.split(chr(10)))}")

    # Verifica risultati
    issues = []

    if result.lower().startswith("certamente"):
        issues.append("❌ Inizia ancora con 'Certamente'")

    if result.lower().startswith("ecco"):
        issues.append("❌ Inizia ancora con 'Ecco'")

    if "\n\n" in result:
        issues.append("⚠️  Doppi a capo ancora presenti")

    if not result.startswith("💥"):
        issues.append("⚠️  Non inizia con l'emoji (dovrebbe essere il primo carattere)")

    lines = result.split("\n")
    expected_lines = 5  # 5 frasi principali

    if len(lines) > expected_lines + 2:
        issues.append(f"⚠️  Troppe righe: {len(lines)} (attese ~{expected_lines})")

    print(f"\n📊 ANALISI:")
    print(f"   - Inizia con: '{result[:30]}'")
    print(f"   - Righe totali: {len(lines)}")
    print(f"   - Doppi a capo: {'NO ✅' if chr(10)*2 not in result else 'SI ⚠️'}")

    if issues:
        print(f"\n⚠️  PROBLEMI TROVATI:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print(f"\n✅ PASS - Formato perfetto!")
        return True


def main():
    print("🔍 TEST SUITE: format_summary_text - LLM Intro & Spacing")
    print("=" * 70)

    results = []

    results.append(("LLM Intro Removal", test_llm_intro_removal()))
    results.append(("Excessive Spacing", test_excessive_spacing()))
    results.append(("Abbreviations Preserved", test_abbreviations_preserved()))
    results.append(("Real World Example", test_real_world_example()))

    # Riepilogo
    print("\n\n" + "=" * 70)
    print("📊 RIEPILOGO TEST")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)

    print(f"\n🎯 Risultato: {passed_count}/{total} test passati")

    if passed_count == total:
        print("\n🎉 TUTTI I TEST SUPERATI!")
        print("\n💡 Il bot ora:")
        print("   ✅ Rimuove introduzioni del LLM")
        print("   ✅ Elimina spazi eccessivi")
        print("   ✅ Preserva abbreviazioni")
        print("   ✅ Formatta correttamente per Telegram")
    else:
        print("\n⚠️  ALCUNI TEST FALLITI")

    print("=" * 70)


if __name__ == "__main__":
    main()
