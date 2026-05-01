"""
PiGenus Philosophy Module

Dieses Modul definiert die fünf Grundfunktionen von PiGenus und stellt sicher,
dass alle Komponenten diesen Prinzipien folgen.

PiGenus ist der dauerhaft verfügbare, private Infrastruktur-Kern des GENUS-Systems,
betrieben auf energieeffizienter lokaler Hardware (primär Raspberry Pi), der:
- Erinnerung, Koordination, Verwaltung, sichere Erreichbarkeit und systemübergreifende Orchestrierung übernimmt.
- KEIN einzelner Chatbot, KEIN primäres Sprachmodell und KEIN Hochleistungsrechner ist.
- Die stabile Basisschicht ist, auf der wechselnde Intelligenzen, Worker, Geräte und Dienste organisiert zusammenarbeiten.
"""

from enum import Enum
from typing import List, Dict, Any, Optional


class PiGenusPrinciple(Enum):
    """
    Die fünf Grundfunktionen von PiGenus.
    Jede Komponente von PiGenus sollte mindestens einem dieser Prinzipien dienen.
    """
    PERSISTENCE = "persistenz"
    ORCHESTRATION = "orchestrierung"
    ADMINISTRATION = "administration"
    INTERFACING = "schnittstellenfaehigkeit"
    CONTINUITY = "kontinuität"


class PiGenusPhilosophy:
    """
    Kernphilosophie von PiGenus.
    
    PiGenus erfüllt fünf Grundfunktionen:
    1. Persistenz: Bewahrt Zustände über Zeit.
    2. Orchestrierung: Verteilt Arbeit intelligent an geeignete Ressourcen.
    3. Administration: Verwaltet das Gesamtsystem.
    4. Schnittstellenfähigkeit: Verbindet unterschiedliche Geräte, Dienste und Instanzen.
    5. Kontinuität: Läuft dauerhaft, verlässlich und ressourcenschonend.
    
    Betriebsphilosophie:
    - Nicht maximale Leistung, sondern maximale Verlässlichkeit.
    - Nicht alles selbst tun, sondern alles sinnvoll koordinieren.
    - Nicht kurzfristig beeindrucken, sondern langfristig tragen.
    """

    PRINCIPLES: Dict[PiGenusPrinciple, Dict[str, Any]] = {
        PiGenusPrinciple.PERSISTENCE: {
            "name": "Persistenz",
            "description": "Bewahrt Zustände über Zeit. GENUS beginnt nicht bei jeder Sitzung neu.",
            "goals": [
                "Erinnerungen speichern",
                "Verläufe dokumentieren",
                "Konfigurationen verwalten",
                "Aufgabenstände tracken",
                "Entscheidungen protokollieren",
                "Projektdaten bewahren",
                "Protokolle führen",
                "Wissensverdichtungen erstellen"
            ],
            "implementation": [
                {
                    "component": "db/models.py (MemoryItem)",
                    "description": "Langzeitspeicher für beliebige Key-Value-Daten (JSON)"
                },
                {
                    "component": "db/models.py (Session + Message)",
                    "description": "Sitzungsverläufe mit Nachrichtenhistorie"
                },
                {
                    "component": "core/config.py (Settings)",
                    "description": "Zentrale Konfiguration mit Umgebungsvariablen"
                },
                {
                    "component": "db/models.py (Job)",
                    "description": "Aufgabenstände mit Status-Tracking"
                },
                {
                    "component": "db/models.py (AuditLog)",
                    "description": "Protokoll aller Systemaktionen"
                },
                {
                    "component": "memory/summarizer.py",
                    "description": "Automatische Wissensverdichtung (Session-Zusammenfassungen)"
                }
            ],
            "endpoints": [
                "/memory/set",
                "/memory/get",
                "/memory/list"
            ]
        },
        PiGenusPrinciple.ORCHESTRATION: {
            "name": "Orchestrierung",
            "description": "Verteilt Arbeit intelligent an geeignete Ressourcen. PiGenus muss nicht alles selbst tun, sondern das Richtige veranlassen.",
            "goals": [
                "Worker auswählen",
                "Aufgaben zuweisen",
                "Ergebnisse entgegennehmen",
                "Abläufe koordinieren",
                "Prioritäten verwalten",
                "Ressourcen nutzen",
                "Zeitfenster planen"
            ],
            "implementation": [
                {
                    "component": "api/endpoints/workers.py",
                    "description": "Worker-Registrierung und Heartbeat"
                },
                {
                    "component": "api/endpoints/jobs.py",
                    "description": "Job-Submit, Lease, Ack/Fail"
                },
                {
                    "component": "db/models.py (Job.priority)",
                    "description": "Prioritätsverwaltung für Jobs"
                },
                {
                    "component": "db/models.py (JobStatus)",
                    "description": "Job-Lebenszyklus (PENDING → LEASED → RUNNING → COMPLETED/FAILED)"
                },
                {
                    "component": "workers/client.py",
                    "description": "Referenzimplementierung für Worker"
                }
            ],
            "endpoints": [
                "/workers/register",
                "/workers/heartbeat",
                "/workers/list",
                "/jobs/submit",
                "/jobs/lease",
                "/jobs/{id}/ack",
                "/jobs/{id}/fail"
            ]
        },
        PiGenusPrinciple.ADMINISTRATION: {
            "name": "Administration",
            "description": "Verwaltet das Gesamtsystem. PiGenus ist die Betriebsführung des Systems.",
            "goals": [
                "Benutzerrechte verwalten",
                "Gerätevertrauen sicherstellen",
                "Systemregeln durchsetzen",
                "Versionen verwalten",
                "Backups erstellen",
                "Status überwachen",
                "Fehler behandeln",
                "Sicherheitsrichtlinien durchsetzen"
            ],
            "implementation": [
                {
                    "component": "api/auth.py",
                    "description": "JWT-Authentifizierung und Token-Verwaltung"
                },
                {
                    "component": "db/models.py (User)",
                    "description": "Benutzerverwaltung mit Rollen (Admin/User)"
                },
                {
                    "component": "api/endpoints/admin.py",
                    "description": "Admin-Endpunkte für Systemstatus und -verwaltung"
                },
                {
                    "component": "services/backup.py",
                    "description": "Backup-Service für Datenbank und Konfiguration"
                },
                {
                    "component": "services/audit.py",
                    "description": "Audit-Logging für alle Systemaktionen"
                },
                {
                    "component": "api/endpoints/health.py",
                    "description": "Health-Checks für Systemmonitoring"
                }
            ],
            "endpoints": [
                "/auth/token",
                "/admin/status",
                "/admin/audit-logs",
                "/admin/users",
                "/health"
            ]
        },
        PiGenusPrinciple.INTERFACING: {
            "name": "Schnittstellenfähigkeit",
            "description": "Verbindet unterschiedliche Geräte, Dienste und Instanzen. PiGenus ist der Knotenpunkt des Netzwerks.",
            "goals": [
                "Handy anbinden",
                "Laptop integrieren",
                "Worker-Rechner einbinden",
                "Cloud-Dienste verbinden",
                "APIs bereitstellen",
                "GitHub integrieren",
                "Smart-Home-Systeme anbinden",
                "Weitere GENUS-Module verbinden"
            ],
            "implementation": [
                {
                    "component": "api/main.py (FastAPI)",
                    "description": "REST-API für universelle Anbindung"
                },
                {
                    "component": "workers/client.py",
                    "description": "Worker-Client-Bibliothek für einfache Integration"
                },
                {
                    "component": "models/schemas.py",
                    "description": "Pydantic-Schemas für standardisierte Kommunikation"
                },
                {
                    "component": "db/models.py (Worker.capabilities)",
                    "description": "Worker melden ihre Fähigkeiten (JSON)"
                }
            ],
            "endpoints": [
                "/health",
                "/auth/token",
                "/workers/register",
                "/jobs/submit",
                "/jobs/lease",
                "/memory/set",
                "/memory/get"
            ]
        },
        PiGenusPrinciple.CONTINUITY: {
            "name": "Kontinuität",
            "description": "Läuft dauerhaft, verlässlich und ressourcenschonend. PiGenus verkörpert Beständigkeit.",
            "goals": [
                "24/7 Verfügbarkeit",
                "Geringer Stromverbrauch",
                "Automatische Wiederherstellung",
                "Regelmäßige Wartung",
                "Zeitgesteuerte Hintergrundarbeit",
                "Langfristige Stabilität"
            ],
            "implementation": [
                {
                    "component": "systemd/pigenus.service",
                    "description": "systemd-Service für Hauptanwendung (24/7-Betrieb)"
                },
                {
                    "component": "systemd/pigenus-scheduler.service",
                    "description": "systemd-Service für Nachtjobs"
                },
                {
                    "component": "core/scheduler.py",
                    "description": "APScheduler für zeitgesteuerte Aufgaben"
                },
                {
                    "component": "db/database.py (SQLite)",
                    "description": "Energieeffiziente, dateibasierte Datenbank"
                },
                {
                    "component": "monitoring/health.py",
                    "description": "Health-Checks für Systemstabilität"
                },
                {
                    "component": "scripts/nightly_jobs.sh",
                    "description": "Skript für tägliche Wartungsaufgaben"
                }
            ],
            "endpoints": [
                "/health"
            ]
        }
    }

    # Was PiGenus NICHT ist
    NOT_PRINCIPLES: List[str] = [
        "Kein Haupt-LLM (PiGenus koordiniert nur – die Intelligenz liegt in den Workern)",
        "Kein GPU-Cluster (PiGenus verwendet keine GPU – Worker können GPU-nutzende Aufgaben erhalten)",
        "Kein reines Frontend (PiGenus ist eine API + Hintergrunddienste)",
        "Kein Wegwerf-Projekt (PiGenus ist langfristig stabil und wartbar)",
        "Kein bloßer Raspberry-Pi-Spielversuch (PiGenus ist produktionsreif)",
        "Kein autonomer Selbstzweck (PiGenus dient dem GENUS-Ökosystem)"
    ]

    # Betriebsphilosophie
    OPERATING_PRINCIPLES: List[str] = [
        "Nicht maximale Leistung, sondern maximale Verlässlichkeit.",
        "Nicht alles selbst tun, sondern alles sinnvoll koordinieren.",
        "Nicht kurzfristig beeindrucken, sondern langfristig tragen."
    ]

    # Zeitliche Rollen
    TIME_MODES: Dict[str, Dict[str, Any]] = {
        "realtime": {
            "description": "Echtzeitmodus – Sofortige Verarbeitung von Anfragen.",
            "activities": [
                "Anfragen annehmen",
                "Jobs koordinieren",
                "Status liefern",
                "Antworten vermitteln",
                "Sicherheit prüfen"
            ],
            "components": [
                "FastAPI (api/main.py)",
                "Authentifizierung (api/auth.py)",
                "Worker-Endpunkte (api/endpoints/workers.py)",
                "Job-Endpunkte (api/endpoints/jobs.py)"
            ]
        },
        "background": {
            "description": "Hintergrundmodus – Geplante Wartungsaufgaben.",
            "activities": [
                "Gedächtnis verdichten",
                "Backups erstellen",
                "Logs bereinigen",
                "Aufgaben vorbereiten",
                "Daten synchronisieren",
                "Berichte erzeugen",
                "Optimierungen anstoßen"
            ],
            "components": [
                "APScheduler (core/scheduler.py)",
                "BackupService (services/backup.py)",
                "AuditService (services/audit.py)",
                "SessionSummarizer (memory/summarizer.py)"
            ]
        }
    }

    @classmethod
    def get_principle(cls, principle: PiGenusPrinciple) -> Dict[str, Any]:
        """
        Gibt die Details zu einem Prinzip zurück.
        
        Args:
            principle: Das gewünschte Prinzip (PiGenusPrinciple Enum)
            
        Returns:
            Dictionary mit Details zum Prinzip
        """
        return cls.PRINCIPLES.get(principle, {})

    @classmethod
    def get_principle_by_name(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Gibt die Details zu einem Prinzip basierend auf dem Namen zurück.
        
        Args:
            name: Der Name des Prinzips (z.B. "persistenz")
            
        Returns:
            Dictionary mit Details zum Prinzip oder None
        """
        for principle, details in cls.PRINCIPLES.items():
            if principle.value == name:
                return details
        return None

    @classmethod
    def get_all_principles(cls) -> Dict[PiGenusPrinciple, Dict[str, Any]]:
        """
        Gibt alle Prinzipien zurück.
        
        Returns:
            Dictionary mit allen Prinzipien
        """
        return cls.PRINCIPLES

    @classmethod
    def validate_component(cls, component: str, principle: PiGenusPrinciple) -> bool:
        """
        Prüft, ob eine Komponente zu einem Prinzip gehört.
        
        Args:
            component: Der Name der Komponente (z.B. "db/models.py")
            principle: Das Prinzip, das geprüft werden soll
            
        Returns:
            True, wenn die Komponente zum Prinzip gehört
        """
        implementation = cls.PRINCIPLES[principle].get("implementation", [])
        return any(component in impl["component"] for impl in implementation)

    @classmethod
    def get_principles_for_component(cls, component: str) -> List[PiGenusPrinciple]:
        """
        Gibt alle Prinzipien zurück, zu denen eine Komponente gehört.
        
        Args:
            component: Der Name der Komponente
            
        Returns:
            Liste der Prinzipien, zu denen die Komponente gehört
        """
        principles = []
        for principle, details in cls.PRINCIPLES.items():
            if cls.validate_component(component, principle):
                principles.append(principle)
        return principles

    @classmethod
    def get_endpoints_for_principle(cls, principle: PiGenusPrinciple) -> List[str]:
        """
        Gibt alle Endpunkte zurück, die zu einem Prinzip gehören.
        
        Args:
            principle: Das gewünschte Prinzip
            
        Returns:
            Liste der Endpunkte
        """
        return cls.PRINCIPLES[principle].get("endpoints", [])

    @classmethod
    def get_goals_for_principle(cls, principle: PiGenusPrinciple) -> List[str]:
        """
        Gibt alle Ziele für ein Prinzip zurück.
        
        Args:
            principle: Das gewünschte Prinzip
            
        Returns:
            Liste der Ziele
        """
        return cls.PRINCIPLES[principle].get("goals", [])

    @classmethod
    def get_implementation_for_principle(cls, principle: PiGenusPrinciple) -> List[Dict[str, str]]:
        """
        Gibt alle Implementierungen für ein Prinzip zurück.
        
        Args:
            principle: Das gewünschte Prinzip
            
        Returns:
            Liste der Implementierungen
        """
        return cls.PRINCIPLES[principle].get("implementation", [])


# Beispielnutzung:
# from core.philosophy import PiGenusPhilosophy, PiGenusPrinciple
# 
# # Alle Prinzipien anzeigen
# for principle, details in PiGenusPhilosophy.get_all_principles().items():
#     print(f"{principle.value}: {details['name']}")
# 
# # Prüfen, ob eine Komponente zu einem Prinzip gehört
# is_persistence = PiGenusPhilosophy.validate_component("db/models.py", PiGenusPrinciple.PERSISTENCE)
# 
# # Alle Endpunkte für ein Prinzip anzeigen
# endpoints = PiGenusPhilosophy.get_endpoints_for_principle(PiGenusPrinciple.ORCHESTRATION)
