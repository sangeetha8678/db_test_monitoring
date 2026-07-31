"""
Base TelemetryRepository Abstract Class.
Defines the standard data-access interface for both PostgreSQL and SQLite fallback repositories.
"""

from abc import ABC, abstractmethod

class TelemetryRepository(ABC):
    @abstractmethod
    def execute_query(self, query, params=None):
        """Executes a SQL query and returns dict with success, columns, rows."""
        pass

    @abstractmethod
    def get_latest_timestamp(self, table="energymeter", device_id=None):
        """Returns the latest available timestamp string for dataset-relative time windows."""
        pass

    @abstractmethod
    def list_devices(self, table="energymeter"):
        """Returns list of distinct device IDs."""
        pass

    @abstractmethod
    def get_telemetry_window(self, table="energymeter", device_id=None, hours=None, limit=1000):
        """Returns telemetry rows within a dataset-relative time window."""
        pass

    @abstractmethod
    def is_live(self):
        """Returns True if connected to PostgreSQL primary DB, False if fallback SQLite."""
        pass
