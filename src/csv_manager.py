import pandas as pd
import os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def save_data(name, data_list):
    """
    Nimmt eine Liste von Dictionaries und speichert sie als CSV.
    LÖSCHT die Datei, wenn keine Daten vorhanden sind (z.B. CWL vorbei).
    """
    file_path = os.path.join(DATA_DIR, f"{name}.csv")

    # 1. Fall: Keine Daten vorhanden (z.B. keine CWL, Liste ist leer)
    if not data_list:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"ℹ️  Keine Daten für {name} -> Alte Datei gelöscht.")
            except Exception as e:
                print(f"⚠️  Konnte {name}.csv nicht löschen: {e}")
        return

    # Wenn es nur ein einzelnes Dictionary ist (z.B. Basis-Stats), packen wir es in eine Liste
    if isinstance(data_list, dict):
        data_list = [data_list]

    # 2. Fall: Daten vorhanden -> Speichern/Überschreiben
    try:
        df = pd.DataFrame(data_list)
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"✅ {name}.csv gespeichert ({len(df)} Zeilen).")
    except Exception as e:
        print(f"❌ Fehler beim Speichern von {name}: {e}")