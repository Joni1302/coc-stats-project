import matplotlib.pyplot as plt
import pandas as pd
import os

# Definiere den Ordner, in dem die Bilder gespeichert werden sollen
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True) # Erstellt den Ordner, falls er nicht existiert

def plot_trophy_stats(player_data: pd.Series):
    """
    Erstellt ein Balkendiagramm für die aktuellen und besten Trophäen des Spielers
    und speichert es als PNG-Datei.
    """
    
    # 1. Daten für den Plot vorbereiten
    trophies = {
        'Aktuell': player_data['trophies'],
        'Bestmarke': player_data['best_trophies']
    }
    
    # Daten in eine Pandas Series für einfaches Plotten
    trophy_series = pd.Series(trophies)
    
    # 2. Plot erstellen
    plt.figure(figsize=(8, 6)) # Größe des Diagramms
    trophy_series.plot(kind='bar', color=['#3C9D9B', '#F7B731']) # Farben für CoC-Look
    
    # 3. Beschriftungen und Titel
    plt.title(f"Trophäenübersicht von {player_data['name']}", fontsize=16)
    plt.ylabel("Anzahl Trophäen", fontsize=12)
    plt.xticks(rotation=0) # Beschriftungen horizontal halten
    
    # Werte über den Balken anzeigen
    for i, v in enumerate(trophy_series.values):
        plt.text(i, v + 5, str(v), color='black', ha='center', fontweight='bold')
        
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout() # Stellt sicher, dass nichts abgeschnitten wird
    
    # 4. Diagramm speichern
    filename = os.path.join(OUTPUT_DIR, f"{player_data['tag']}_trophy_stats.png")
    plt.savefig(filename)
    plt.close() # Schließt die Figur, um Speicher freizugeben
    
    print(f"✅ Visualisierung gespeichert unter: {filename}")

# Du könntest hier weitere Funktionen für andere Plots (z.B. Angriffs-Siege) hinzufügen.