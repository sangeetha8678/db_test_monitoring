"""
SQLite CSV Telemetry Repository Implementation.
Provides seamless fallback data persistence by loading energymeter_202607301217.csv on startup.
"""

import os
import csv
import re
import sqlite3
from database.repository import TelemetryRepository
from config import CSV_FILE_PATH

class SqliteRepository(TelemetryRepository):
    def __init__(self, csv_path=CSV_FILE_PATH):
        self.csv_path = csv_path
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._load_csv_data()

    def _load_csv_data(self):
        if not os.path.exists(self.csv_path):
            return
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    return

                headers = [c.strip().replace('"', '').lower() for c in header]
                num_cols = [
                    "voltageab", "voltagebc", "voltageca", "voltagean", "voltagebn", "voltagecn",
                    "currenta", "currentb", "currentc", "currentavg", "activepower", "reactivepower",
                    "apparentpower", "powerfactor", "frequency", "importenergykwh"
                ]

                col_defs = ", ".join([f'"{c}" REAL' if c in num_cols else f'"{c}" TEXT' for c in headers])
                self.conn.execute(f'CREATE TABLE energymeter ({col_defs});')
                self.conn.execute(f'CREATE TABLE "public.energymeter" ({col_defs});')

                placeholders = ", ".join(["?"] * len(headers))
                batch = []
                for row in reader:
                    if len(row) == len(headers):
                        parsed_row = []
                        for idx, val in enumerate(row):
                            val_str = val.strip()
                            if val_str == "" or val_str == "NULL":
                                parsed_row.append(None)
                            elif headers[idx] in num_cols:
                                try:
                                    parsed_row.append(float(val_str))
                                except ValueError:
                                    parsed_row.append(None)
                            else:
                                parsed_row.append(val_str)
                        batch.append(parsed_row)

                if batch:
                    self.conn.executemany(f'INSERT INTO energymeter VALUES ({placeholders});', batch)
                    self.conn.executemany(f'INSERT INTO "public.energymeter" VALUES ({placeholders});', batch)
                    self.conn.commit()
                print(f"✅ Loaded {len(batch)} records from {os.path.basename(self.csv_path)} into SQLite Fallback Engine.")
        except Exception as e:
            print(f"Notice: SQLite CSV init: {e}")

    def is_live(self):
        return False  # Fallback engine

    def execute_query(self, query, params=None):
        try:
            clean_q = query.replace('public."', '"').replace('public.', '')
            clean_q = re.sub(r'::double precision|::text|::timestamptz', '', clean_q, flags=re.IGNORECASE)
            clean_q = re.sub(r"WHERE\s+time.+?INTERVAL\s*['\"][^'\"]+['\"]", "WHERE 1=1", clean_q, flags=re.IGNORECASE)
            clean_q = re.sub(r"-\s*INTERVAL\s*['\"][^'\"]+['\"]", "", clean_q, flags=re.IGNORECASE)

            cur = self.conn.cursor()
            if params:
                cur.execute(clean_q, params)
            else:
                cur.execute(clean_q)

            if cur.description:
                columns = [d[0] for d in cur.description]
                rows = cur.fetchall()
                return {"success": True, "columns": columns, "rows": list(rows), "source": "SQLite CSV Fallback"}
            return {"success": True, "columns": [], "rows": [], "source": "SQLite CSV Fallback"}
        except Exception:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT * FROM energymeter ORDER BY time ASC LIMIT 100;")
                columns = [d[0] for d in cur.description]
                rows = cur.fetchall()
                return {"success": True, "columns": columns, "rows": list(rows), "source": "SQLite CSV Fallback"}
            except Exception as e:
                return {"success": False, "error": str(e), "source": "SQLite CSV Fallback"}

    def get_latest_timestamp(self, table="energymeter", device_id=None):
        device_clause = f"WHERE deviceid = '{device_id}'" if device_id else ""
        sql = f'SELECT MAX(time) FROM energymeter {device_clause};'
        res = self.execute_query(sql)
        if res.get("success") and res.get("rows") and res["rows"][0][0]:
            return str(res["rows"][0][0])
        return None

    def list_devices(self, table="energymeter"):
        sql = 'SELECT DISTINCT deviceid FROM energymeter WHERE deviceid IS NOT NULL ORDER BY deviceid;'
        res = self.execute_query(sql)
        if res.get("success") and res.get("rows"):
            return [str(r[0]) for r in res["rows"] if r[0] is not None]
        return []

    def get_telemetry_window(self, table="energymeter", device_id=None, hours=None, limit=1000):
        device_clause = f"AND deviceid = '{device_id}'" if device_id else ""
        sql = f'SELECT * FROM energymeter WHERE 1=1 {device_clause} ORDER BY time ASC LIMIT {int(limit)};'
        return self.execute_query(sql)
