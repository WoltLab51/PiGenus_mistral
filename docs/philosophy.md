# PiGenus Philosophie

## 🎯 Wesensdefinition

**PiGenus ist der dauerhaft verfügbare, private Infrastruktur-Kern des GENUS-Systems**, betrieben auf energieeffizienter lokaler Hardware (primär Raspberry Pi), der:

- **Erinnerung, Koordination, Verwaltung, sichere Erreichbarkeit und systemübergreifende Orchestrierung** übernimmt.

PiGenus ist **KEIN**:
- Einzelner Chatbot
- Primäres Sprachmodell
- Hochleistungsrechner
- Reines Frontend
- Wegwerf-Projekt
- Bloßer Raspberry-Pi-Spielversuch
- Autonomer Selbstzweck

PiGenus ist **die stabile Basisschicht**, auf der wechselnde Intelligenzen, Worker, Geräte und Dienste organisiert zusammenarbeiten.

---

## 🏛️ Die fünf Grundfunktionen

PiGenus erfüllt fünf zentrale Funktionen, die das GENUS-Ökosystem erst ermöglichen:

### 1. 💾 Persistenz
**"Bewahrt Zustände über Zeit. GENUS beginnt nicht bei jeder Sitzung neu."**

#### Ziele
- Erinnerungen speichern
- Verläufe dokumentieren
- Konfigurationen verwalten
- Aufgabenstände tracken
- Entscheidungen protokollieren
- Projektdaten bewahren
- Protokolle führen
- Wissensverdichtungen erstellen

#### Implementierung
| Komponente | Beschreibung |
|------------|--------------|
| `db/models.py (MemoryItem)` | Langzeitspeicher für beliebige Key-Value-Daten (JSON) |
| `db/models.py (Session + Message)` | Sitzungsverläufe mit Nachrichtenhistorie |
| `core/config.py (Settings)` | Zentrale Konfiguration mit Umgebungsvariablen |
| `db/models.py (Job)` | Aufgabenstände mit Status-Tracking |
| `db/models.py (AuditLog)` | Protokoll aller Systemaktionen |
| `memory/summarizer.py` | Automatische Wissensverdichtung (Session-Zusammenfassungen) |

#### API-Endpunkte
- `POST /memory/set` – Wert speichern
- `GET /memory/get/{key}` – Wert abrufen
- `GET /memory/list` – Alle Memory-Items anzeigen

---

### 2. 🎭 Orchestrierung
**"Verteilt Arbeit intelligent an geeignete Ressourcen. PiGenus muss nicht alles selbst tun, sondern das Richtige veranlassen."**

#### Ziele
- Worker auswählen
- Aufgaben zuweisen
- Ergebnisse entgegennehmen
- Abläufe koordinieren
- Prioritäten verwalten
- Ressourcen nutzen
- Zeitfenster planen

#### Implementierung
| Komponente | Beschreibung |
|------------|--------------|
| `api/endpoints/workers.py` | Worker-Registrierung und Heartbeat |
| `api/endpoints/jobs.py` | Job-Submit, Lease, Ack/Fail |
| `db/models.py (Job.priority)` | Prioritätsverwaltung für Jobs |
| `db/models.py (JobStatus)` | Job-Lebenszyklus (PENDING → LEASED → RUNNING → COMPLETED/FAILED) |
| `workers/client.py` | Referenzimplementierung für Worker |

#### API-Endpunkte
- `POST /workers/register` – Worker registrieren
- `POST /workers/heartbeat` – Worker-Status aktualisieren
- `GET /workers/list` – Alle Worker anzeigen
- `POST /jobs/submit` – Job einreichen
- `GET /jobs/lease` – Job leasen
- `POST /jobs/{id}/ack` – Job bestätigen
- `POST /jobs/{id}/fail` – Job als fehlgeschlagen melden

---

### 3. 🛠️ Administration
**"Verwaltet das Gesamtsystem. PiGenus ist die Betriebsführung des Systems."**

#### Ziele
- Benutzerrechte verwalten
- Gerätevertrauen sicherstellen
- Systemregeln durchsetzen
- Versionen verwalten
- Backups erstellen
- Status überwachen
- Fehler behandeln
- Sicherheitsrichtlinien durchsetzen

#### Implementierung
| Komponente | Beschreibung |
|------------|--------------|
| `api/auth.py` | JWT-Authentifizierung und Token-Verwaltung |
| `db/models.py (User)` | Benutzerverwaltung mit Rollen (Admin/User) |
| `api/endpoints/admin.py` | Admin-Endpunkte für Systemstatus und -verwaltung |
| `services/backup.py` | Backup-Service für Datenbank und Konfiguration |
| `services/audit.py` | Audit-Logging für alle Systemaktionen |
| `api/endpoints/health.py` | Health-Checks für Systemmonitoring |

#### API-Endpunkte
- `POST /auth/token` – JWT-Token generieren
- `GET /admin/status` – Systemstatus abrufen
- `GET /admin/audit-logs` – Audit-Logs anzeigen
- `GET /admin/users` – Benutzerliste abrufen
- `GET /health` – Health-Check

---

### 4. 🌐 Schnittstellenfähigkeit
**"Verbindet unterschiedliche Geräte, Dienste und Instanzen. PiGenus ist der Knotenpunkt des Netzwerks."**

#### Ziele
- Handy anbinden
- Laptop integrieren
- Worker-Rechner einbinden
- Cloud-Dienste verbinden
- APIs bereitstellen
- GitHub integrieren (geplant)
- Smart-Home-Systeme anbinden (geplant)
- Weitere GENUS-Module verbinden

#### Implementierung
| Komponente | Beschreibung |
|------------|--------------|
| `api/main.py (FastAPI)` | REST-API für universelle Anbindung |
| `workers/client.py` | Worker-Client-Bibliothek für einfache Integration |
| `models/schemas.py` | Pydantic-Schemas für standardisierte Kommunikation |
| `db/models.py (Worker.capabilities)` | Worker melden ihre Fähigkeiten (JSON) |

#### API-Endpunkte
- `GET /health` – System-Health-Check
- `POST /auth/token` – Authentifizierung
- `POST /workers/register` – Worker registrieren
- `POST /jobs/submit` – Job einreichen
- `GET /jobs/lease` – Job leasen
- `POST /memory/set` – Memory-Item speichern
- `GET /memory/get/{key}` – Memory-Item abrufen

---

### 5. ⚡ Kontinuität
**"Läuft dauerhaft, verlässlich und ressourcenschonend. PiGenus verkörpert Beständigkeit."**

#### Ziele
- 24/7 Verfügbarkeit
- Geringer Stromverbrauch
- Automatische Wiederherstellung
- Regelmäßige Wartung
- Zeitgesteuerte Hintergrundarbeit
- Langfristige Stabilität

#### Implementierung
| Komponente | Beschreibung |
|------------|--------------|
| `systemd/pigenus.service` | systemd-Service für Hauptanwendung (24/7-Betrieb) |
| `systemd/pigenus-scheduler.service` | systemd-Service für Nachtjobs |
| `core/scheduler.py` | APScheduler für zeitgesteuerte Aufgaben |
| `db/database.py (SQLite)` | Energieeffiziente, dateibasierte Datenbank |
| `monitoring/health.py` | Health-Checks für Systemstabilität |
| `scripts/nightly_jobs.sh` | Skript für tägliche Wartungsaufgaben |

#### API-Endpunkte
- `GET /health` – Systemstatus abrufen

---

## 🧭 Betriebsphilosophie

PiGenus folgt diesen **drei Grundsätzen**:

1. **"Nicht maximale Leistung, sondern maximale Verlässlichkeit."**
   - PiGenus ist für **Stabilität und Dauerbetrieb** optimiert, nicht für Hochleistung.
   - Beispiel: SQLite statt PostgreSQL (für MVP), systemd für automatische Wiederherstellung.

2. **"Nicht alles selbst tun, sondern alles sinnvoll koordinieren."**
   - PiGenus **delegiert** Aufgaben an Worker (Laptops, Cloud, etc.).
   - Beispiel: Job-Leasing (`/jobs/lease`) statt eigene Ausführung.

3. **"Nicht kurzfristig beeindrucken, sondern langfristig tragen."**
   - PiGenus ist für **langfristigen Einsatz** ausgelegt.
   - Beispiel: Nachtjobs für Wartung, Backups, Log-Rotation.

---

## ⏳ Zeitliche Rollen

PiGenus arbeitet in **zwei Modi**:

### 🔄 Echtzeitmodus
**"Sofortige Verarbeitung von Anfragen."**

#### Aktivitäten
- Anfragen annehmen
- Jobs koordinieren
- Status liefern
- Antworten vermitteln
- Sicherheit prüfen

#### Komponenten
- FastAPI (`api/main.py`)
- Authentifizierung (`api/auth.py`)
- Worker-Endpunkte (`api/endpoints/workers.py`)
- Job-Endpunkte (`api/endpoints/jobs.py`)

---

### 🌙 Hintergrundmodus
**"Geplante Wartungsaufgaben."**

#### Aktivitäten
- Gedächtnis verdichten
- Backups erstellen
- Logs bereinigen
- Aufgaben vorbereiten
- Daten synchronisieren
- Berichte erzeugen
- Optimierungen anstoßen

#### Komponenten
- APScheduler (`core/scheduler.py`)
- BackupService (`services/backup.py`)
- AuditService (`services/audit.py`)
- SessionSummarizer (`memory/summarizer.py`)

---

## 🏗️ Technische Essenz

PiGenus ist architektonisch ein:

- **Persistent Orchestration Node** (Englisch)
- **Dauerhafter Koordinations- und Gedächtnisknoten** (Deutsch)

### Vergleich: GENUS vs. PiGenus
| GENUS | PiGenus |
|-------|---------|
| **Organismus** | **Rückenmark + Gedächtnis + Kreislauf + Leitstand** |
| Gesamtsystem intelligenter Fähigkeiten und Erlebnisse | Lokaler, verlässlicher Kern |
| Enthält alle Module (LLMs, Worker, Clients) | Koordiniert die Module |
| Dynamisch und erweiterbar | Stabil und dauerhaft |

---

## 📜 Endgültige Kurzdefinition

> **PiGenus ist die stets verfügbare, private Kerninstanz von GENUS, die Informationen bewahrt, Arbeit organisiert, Systeme verbindet und langfristige Kontinuität sicherstellt.**

---

## 🔗 Beziehung zu anderen Systemen

### Was PiGenus **ist**:
- Ein **Orchestrierungs-Knoten** für das GENUS-Ökosystem.
- Ein **Persistenz-Layer** für langfristige Daten.
- Ein **Koordinations-Hub** für Worker und Dienste.
- Ein **Administrations-Tool** für Systemmanagement.
- Ein **Kontinuitäts-Garant** für 24/7-Betrieb.

### Was PiGenus **nicht ist**:
- ❌ Ein Haupt-LLM (die Intelligenz liegt in den Workern).
- ❌ Ein GPU-Cluster (PiGenus nutzt keine GPU – Worker können das).
- ❌ Ein reines Frontend (PiGenus ist eine API + Hintergrunddienste).
- ❌ Ein Wegwerf-Projekt (PiGenus ist langfristig stabil).
- ❌ Ein bloßer Raspberry-Pi-Spielversuch (PiGenus ist produktionsreif).
- ❌ Ein autonomer Selbstzweck (PiGenus dient dem GENUS-Ökosystem).

---

## 📚 Weiterführende Dokumentation

- [Architektur](architecture.md) – Technische Details der Implementierung
- [API-Dokumentation](api.md) – Beschreibung aller Endpunkte
- [Deployment-Anleitung](deployment.md) – Installation und Betrieb
