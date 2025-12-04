import pandas as pd
import os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def save_data(name, data_list):
    """
    Nimmt eine Liste von Dictionaries (oder ein Dict) und speichert sie als CSV.
    Überschreibt die Datei jedes Mal.
    """
    if not data_list:
        print(f"Keine Daten für {name} vorhanden, überspringe Speichern.")
        return

    # Wenn es nur ein einzelnes Dictionary ist (z.B. Basis-Stats), packen wir es in eine Liste
    if isinstance(data_list, dict):
        data_list = [data_list]

    try:
        df = pd.DataFrame(data_list)
        file_path = os.path.join(DATA_DIR, f"{name}.csv")
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"💾 {name}.csv erfolgreich gespeichert ({len(df)} Zeilen).")
    except Exception as e:
        print(f"Fehler beim Speichern von {name}: {e}")