# PiGenus

**Der dauerhaft verfügbare, private Infrastruktur-Kern des GENUS-Systems**

---

## 🎯 Philosophie

PiGenus ist **der dauerhaft verfügbare, private Infrastruktur-Kern** des GENUS-Systems, betrieben auf energieeffizienter lokaler Hardware (primär Raspberry Pi), der:

- **Erinnerung, Koordination, Verwaltung, sichere Erreichbarkeit und systemübergreifende Orchestrierung** übernimmt.

PiGenus ist **KEIN**:
- Einzelner Chatbot
- Primäres Sprachmodell
- Hochleistungsrechner
- Reines Frontend
- Wegwerf-Projekt
- Bloßer Raspberry-Pi-Spielversuch
- Autonomer Selbstzweck

> **Betriebsphilosophie**:
> *"Nicht maximale Leistung, sondern maximale Verlässlichkeit.*
> *Nicht alles selbst tun, sondern alles sinnvoll koordinieren.*
> *Nicht kurzfristig beeindrucken, sondern langfristig tragen."*

---

## 🏛️ Die fünf Grundfunktionen

PiGenus erfüllt fünf zentrale Funktionen, die das GENUS-Ökosystem erst ermöglichen:

| Funktion | Beschreibung | Implementierung |
|----------|--------------|----------------|
| **💾 Persistenz** | Bewahrt Zustände über Zeit (Erinnerungen, Verläufe, Konfigurationen, Aufgabenstände). | `MemoryItem`, `Session`, `AuditLog` |
| **🎭 Orchestrierung** | Verteilt Arbeit intelligent an geeignete Ressourcen. | `Worker`, `Job`, Prioritäten |
| **🛠️ Administration** | Verwaltet das Gesamtsystem (Benutzer, Geräte, Regeln, Backups). | JWT-Auth, Admin-Endpunkte |
| **🌐 Schnittstellenfähigkeit** | Verbindet unterschiedliche Geräte, Dienste und Instanzen. | REST-API, Worker-Client |
| **⚡ Kontinuität** | Läuft dauerhaft, verlässlich und ressourcenschonend. | systemd, APScheduler |

**→ [Detaillierte Philosophie](docs/philosophy.md)**

---

## 📌 Wesensdefinition

PiGenus ist **die stabile Basisschicht**, auf der wechselnde Intelligenzen, Worker, Geräte und Dienste organisiert zusammenarbeiten.

| GENUS | PiGenus |
|-------|---------|
| Organismus | Rückenmark + Gedächtnis + Kreislauf + Leitstand |
| Gesamtsystem intelligenter Fähigkeiten und Erlebnisse | Lokaler, verlässlicher Kern |
| Enthält alle Module (LLMs, Worker, Clients) | Koordiniert die Module |

---

## 🚀 Schnellstart

### 1. Repository klonen
```bash
git clone https://github.com/WoltLab51/PiGenus_mistral.git
cd PiGenus_mistral
```

### 2. Abhängigkeiten installieren
```bash
python -m pip install -r requirements.txt
```

### 3. Umgebungsvariablen konfigurieren
```bash
cp .env.example .env
# .env anpassen (SECRET_KEY, DATABASE_URL, etc.)
```

### 4. Datenbank initialisieren
```bash
python scripts/init_db.py
```

### 5. PiGenus starten (Development)
```bash
uvicorn api.main:app --reload
```

### 6. Mit systemd deployen (Production)
```bash
# Services kopieren
sudo cp systemd/pigenus.service /etc/systemd/system/
sudo cp systemd/pigenus-scheduler.service /etc/systemd/system/

# Services aktivieren und starten
sudo systemctl daemon-reload
sudo systemctl enable pigenus pigenus-scheduler
sudo systemctl start pigenus pigenus-scheduler
```

---

## 📡 API-Dokumentation

Die API ist verfügbar unter:
- **Swagger UI**: `http://<host>:8000/docs`
- **ReDoc**: `http://<host>:8000/redoc`

### Endpunkte (nach Grundfunktionen gruppiert)

#### 💾 Persistenz
| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/memory/set` | POST | Memory-Item speichern |
| `/memory/get/{key}` | GET | Memory-Item abrufen |
| `/memory/list` | GET | Alle Memory-Items anzeigen |

#### 🎭 Orchestrierung
| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/workers/register` | POST | Worker registrieren |
| `/workers/heartbeat` | POST | Worker-Heartbeat senden |
| `/workers/list` | GET | Alle Worker anzeigen |
| `/jobs/submit` | POST | Job einreichen |
| `/jobs/lease` | GET | Job leasen |
| `/jobs/{id}/ack` | POST | Job bestätigen |
| `/jobs/{id}/fail` | POST | Job als fehlgeschlagen melden |
| `/jobs/list` | GET | Jobs auflisten |

#### 🛠️ Administration
| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/auth/token` | POST | JWT-Token generieren |
| `/admin/status` | GET | Systemstatus abrufen |
| `/admin/audit-logs` | GET | Audit-Logs anzeigen |
| `/admin/users` | GET | Benutzerliste abrufen |

#### 🌐 Schnittstellenfähigkeit
| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | Health-Check |

#### ⚡ Kontinuität
| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | System-Health-Status |

---

## 📂 Projektstruktur

```
pigenus/
├── .env.example                  # Umgebungsvariablen-Vorlage
├── .gitignore                    # Git-Ignore-Regeln
├── LICENSE                       # MIT-Lizenz
├── README.md                     # Hauptdokumentation
├── pyproject.toml                # Python-Projektkonfiguration
├── requirements.txt              # Abhängigkeiten
│
├── api/                          # FastAPI-Endpunkte
│   ├── __init__.py
│   ├── main.py                   # Hauptanwendung
│   ├── auth.py                   # JWT-Authentifizierung
│   ├── dependencies.py           # Abhängigkeiten-Injection
│   ├── middleware.py             # Rate Limiting & Logging
│   └── endpoints/
│       ├── health.py             # /health (Kontinuität)
│       ├── auth.py               # /auth/token (Administration)
│       ├── workers.py            # /workers/* (Orchestrierung)
│       ├── jobs.py               # /jobs/* (Orchestrierung)
│       ├── memory.py             # /memory/* (Persistenz)
│       └── admin.py              # /admin/* (Administration)
│
├── core/                         # Kernlogik
│   ├── __init__.py
│   ├── philosophy.py             # 🎯 Philosophie & Prinzipien
│   ├── config.py                 # Einstellungen (Pydantic)
│   ├── scheduler.py              # Nachtjobs (Kontinuität)
│   └── ...
│
├── db/                           # Datenbank
│   ├── __init__.py
│   ├── database.py               # SQLite-Verbindung
│   └── models.py                 # SQLModel-Entitäten (Persistenz)
│
├── models/                       # Pydantic-Schemas
│   ├── __init__.py
│   ├── schemas.py                # Request/Response-Schemas
│   └── enums.py                  # Status-Enums
│
├── workers/                      # Worker-Integration
│   ├── __init__.py
│   └── client.py                 # Worker-Client (Schnittstellenfähigkeit)
│
├── memory/                       # Langzeitspeicher
│   ├── __init__.py
│   ├── storage.py                # Memory-Speicher (Persistenz)
│   └── summarizer.py             # Session-Zusammenfassung (Persistenz)
│
├── security/                     # Sicherheit
│   ├── __init__.py
│   ├── tokens.py                 # JWT-Token-Verwaltung
│   └── validation.py             # Input-Validation
│
├── services/                     # Hintergrunddienste
│   ├── __init__.py
│   ├── audit.py                  # Audit-Logs (Administration)
│   └── backup.py                 # Backup-Logik (Kontinuität)
│
├── monitoring/                   # Überwachung
│   ├── __init__.py
│   ├── health.py                 # Health-Checks (Kontinuität)
│   └── metrics.py                # Prometheus-Metriken
│
├── tests/                        # Tests
│   ├── __init__.py
│   ├── conftest.py               # pytest-Fixtures
│   ├── test_api.py               # API-Tests
│   ├── test_core.py              # Core-Logik-Tests
│   └── test_db.py                # DB-Tests
│
├── docs/                         # Dokumentation
│   ├── philosophy.md             # 🎯 Philosophie (detailliert)
│   ├── architecture.md           # Architektur
│   ├── api.md                    # API-Dokumentation
│   └── deployment.md             # Deployment-Anleitung
│
├── scripts/                      # Skripte
│   ├── __init__.py
│   ├── init_db.py                # DB-Initialisierung
│   └── nightly_jobs.sh           # Nachtjobs (Kontinuität)
│
└── systemd/                      # systemd-Services
    ├── pigenus.service            # Haupt-Service (Kontinuität)
    └── pigenus-scheduler.service  # Scheduler-Service (Kontinuität)
```

---

## 🔧 Entwicklung

### Tests ausführen
```bash
pytest -v
```

### Code-Qualität
```bash
black .
isort .
flake8
```

---

## 🔒 Sicherheit

- **Token-Authentifizierung**: Alle Endpunkte (außer `/health`) erfordern ein JWT-Token.
- **Input-Validation**: Alle Requests werden mit Pydantic validiert.
- **Rate Limiting**: Vorbereitet in `api/middleware.py` (deaktiviert per Default).
- **Secrets**: Werden nur über Umgebungsvariablen oder Konfiguration geladen.

---

## 📜 Lizenz

Dieses Projekt steht unter der **MIT-Lizenz** – siehe [LICENSE](LICENSE) für Details.

---

## 📚 Weiterführende Dokumentation

- [🎯 Philosophie](docs/philosophy.md) – Detaillierte Beschreibung der Grundprinzipien
- [🏗️ Architektur](docs/architecture.md) – Technische Details der Implementierung
- [📡 API-Dokumentation](docs/api.md) – Beschreibung aller Endpunkte
- [🚀 Deployment](docs/deployment.md) – Installation und Betrieb
