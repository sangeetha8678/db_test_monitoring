"""
PostgreSQL Telemetry Repository Implementation.
Executes parameterized queries against PostgreSQL primary database.
"""

import os
import subprocess
from database.repository import TelemetryRepository
from config import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD

class PostgresRepository(TelemetryRepository):
    def __init__(self, host=PGHOST, port=PGPORT, dbname=PGDATABASE, user=PGUSER, password=PGPASSWORD):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password

    def is_live(self):
        res = self.execute_query("SELECT 1;")
        return res.get("success", False)

    def execute_query(self, query, params=None):
        # 1. Try psycopg2
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.host, port=self.port, dbname=self.dbname, user=self.user, password=self.password, connect_timeout=2
            )
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    conn.close()
                    return {"success": True, "columns": columns, "rows": list(rows), "source": "PostgreSQL Primary"}
                conn.close()
                return {"success": True, "columns": [], "rows": [], "source": "PostgreSQL Primary"}
        except Exception:
            pass

        # 2. Try psql CLI wrapper
        try:
            env = os.environ.copy()
            if self.password:
                env["PGPASSWORD"] = self.password
            cmd = [
                "psql", "-w", "-h", str(self.host), "-p", str(self.port), "-U", str(self.user), "-d", str(self.dbname),
                "-A", "-F", "\t", "-c", query
            ]
            proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            if proc.returncode == 0:
                lines = proc.stdout.strip().splitlines()
                if lines and lines[-1].startswith("(") and (lines[-1].endswith("rows)") or lines[-1].endswith("row)")):
                    lines.pop()
                if lines:
                    columns = lines[0].split("\t")
                    rows = [line.split("\t") for line in lines[1:] if line]
                    return {"success": True, "columns": columns, "rows": rows, "source": "PostgreSQL CLI Primary"}
        except Exception as e:
            return {"success": False, "error": str(e), "source": "PostgreSQL"}

        return {"success": False, "error": "PostgreSQL connection failed", "source": "PostgreSQL"}

    def get_latest_timestamp(self, table="energymeter", device_id=None):
        device_clause = f"WHERE deviceid = '{device_id}'" if device_id else ""
        sql = f'SELECT MAX(time::text) FROM public."{table}" {device_clause};'
        res = self.execute_query(sql)
        if res.get("success") and res.get("rows") and res["rows"][0][0]:
            return str(res["rows"][0][0])
        return None

    def list_devices(self, table="energymeter"):
        sql = f'SELECT DISTINCT deviceid FROM public."{table}" WHERE deviceid IS NOT NULL ORDER BY deviceid;'
        res = self.execute_query(sql)
        if res.get("success") and res.get("rows"):
            return [str(r[0]) for r in res["rows"] if r[0] is not None]
        return []

    def get_telemetry_window(self, table="energymeter", device_id=None, hours=None, limit=1000):
        device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
        if hours is not None and float(hours) > 0:
            sql = f"""
                SELECT * FROM public."{table}"
                WHERE time::timestamptz >= (SELECT MAX(time::timestamptz) FROM public."{table}") - INTERVAL '{float(hours)} hours' {device_clause}
                ORDER BY time ASC LIMIT {int(limit)};
            """
        else:
            sql = f"""
                SELECT * FROM public."{table}" WHERE 1=1 {device_clause}
                ORDER BY time ASC LIMIT {int(limit)};
            """
        return self.execute_query(sql)
