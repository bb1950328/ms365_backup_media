# Backup-Medium

Dieses Medium enthält Backups eines Microsoft 365-Tenants.
Für das Aktualisieren des Backups ist ein Linux-PC mit folgender Software nötig:
 - Python 3 (sollte vorinstalliert sein)
 - OneDrive-Client (von [abraunegg/onedrive](https://github.com/abraunegg/onedrive))

Die einzelnen `backup_YYYY_MM_DD_HH_MM`-Ordner sind voneinander komplett unabhängig.
Es ist nicht die Idee, den Inhalt dieser Ordner zu verändern, sondern nur neue komplette Ordner erstellen und alte Ordner komplett zu löschen.

## Backup erstellen
1. `./update_configs.py` aufrufen, damit der `sync_dir`-Pfad in der Konfigurationsdatei aktualisiert wird (muss als absoluter Pfad angegeben werden, welcher sich natürlich ändert, wenn das Medium an einem anderen Ort gemountet wird)
2. `./synchronize.py` aufrufen, um die Daten im Ordner `data_current` zu aktualisieren
3. `./copy.sh` aufrufen, um den Ordner `data_current` in einen `backup_YYYY_MM_DD_HH_MM`-Ordner zu kopieren


## Alte Backups löschen
Wenn der Speicherplatz auf dem Medium zur Neige geht, können alte `backup_YYYY_MM_DD_HH_MM`-Ordner gelöscht werden.


## Konfiguration
### Neue SharePoint-Site hinzufügen
1. In `./site_names.csv` den Namen der neuen Site und den Library-Namen (meistens "Dokumente") hinzufügen
2. `./update_sites.py` laufen lassen, um die Datei `./site_names.csv` zu aktualisieren
3. `./update_configs.py` laufen lassen, um die Dateien im Ordner `./config` zu aktualisieren

Hinweis: Das Skript `./update_sites.py` gibt am Schluss eine Liste aller verfügbaren Sites aus, die nicht in der Konfiguration vorkommen

### Sharepoint-Site entfernen
1. In `./site_names.csv` die entsprechende Zeile entfernen
2. In `./sites.csv` die entsprechende Zeile entfernen
3. `./update_configs.py` laufen lassen, um die Dateien im Ordner `./config` zu aktualisieren
