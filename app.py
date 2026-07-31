#!/usr/bin/env python3
"""
PostgreSQL Table Viewer Application
A simple Python application to connect to a local or remote PostgreSQL database
and display all available tables.
"""

import sys
import os
import getpass
import argparse
import subprocess

def load_env_file(env_path=".env"):
    """Loads environment variables from a .env file if it exists."""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = value

load_env_file()


# Terminal Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"

def get_db_connection(host, port, dbname, user, password):
    """
    Attempts to connect to PostgreSQL using psycopg2/psycopg if installed,
    or falls back to libpq (ctypes) or psql CLI.
    """
    # 1. Try psycopg2
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        return ("psycopg2", conn)
    except ImportError:
        pass
    except Exception as e:
        return ("error", str(e))

    # 2. Try psycopg (v3)
    try:
        import psycopg
        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        return ("psycopg", conn)
    except ImportError:
        pass
    except Exception as e:
        return ("error", str(e))

    # 3. Fallback to psql CLI wrapper
    try:
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password
        
        cmd = [
            "psql",
            "-h", host,
            "-p", str(port),
            "-U", user,
            "-d", dbname,
            "-t", "-A", "-F", "\t",
            "-c", "SELECT table_schema, table_name, table_type FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY table_schema, table_name;"
        ]
        
        proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode == 0:
            return ("psql", proc.stdout)
        else:
            return ("error", proc.stderr.strip())
    except Exception as e:
        return ("error", str(e))

def query_tables_python(conn):
    """Queries tables using DB-API cursor."""
    query = """
        SELECT 
            table_schema,
            table_name,
            table_type
        FROM 
            information_schema.tables 
        WHERE 
            table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY 
            table_schema, table_name;
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows

def parse_psql_output(output_text):
    """Parses tab-separated psql output into tuples."""
    rows = []
    for line in output_text.strip().splitlines():
        if line:
            parts = line.split("\t")
            if len(parts) >= 3:
                rows.append((parts[0], parts[1], parts[2]))
            elif len(parts) == 2:
                rows.append(("public", parts[0], parts[1]))
    return rows

def format_table(headers, rows):
    """Formats headers and rows into a nice ASCII table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
            
    header_line = " | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
    separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    
    lines = [f"{BOLD}{CYAN}{header_line}{RESET}", f"{DIM}{separator}{RESET}"]
    for row in rows:
        formatted_row = " | ".join(f"{str(row[i]):<{col_widths[i]}}" for i in range(len(row)))
        lines.append(formatted_row)
        
    return "\n".join(lines)

def prompt_interactive_credentials(default_host, default_port, default_dbname, default_user, default_password):
    """Interactively prompts user for PostgreSQL connection details with default fallback values."""
    print(f"{BOLD}{CYAN}--- Interactive Database Setup ---{RESET}\n")
    
    host_input = input(f"Enter Host [{BOLD}{default_host}{RESET}]: ").strip()
    host = host_input if host_input else default_host
    
    port_input = input(f"Enter Port [{BOLD}{default_port}{RESET}]: ").strip()
    port = port_input if port_input else default_port
    
    dbname_input = input(f"Enter Database Name [{BOLD}{default_dbname}{RESET}]: ").strip()
    dbname = dbname_input if dbname_input else default_dbname
    
    user_input = input(f"Enter Username [{BOLD}{default_user}{RESET}]: ").strip()
    user = user_input if user_input else default_user
    
    prompt_pwd_msg = f"Enter Password (leave blank if none): "
    password = getpass.getpass(prompt=prompt_pwd_msg)
    if not password and default_password:
        password = default_password

    print()
    return host, port, dbname, user, password

def main():
    parser = argparse.ArgumentParser(description="Connect to PostgreSQL and display available tables.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactively prompt for all database connection details")
    parser.add_argument("--host", default=os.getenv("PGHOST", "localhost"), help="PostgreSQL host (default: localhost)")
    parser.add_argument("--port", default=os.getenv("PGPORT", "5432"), help="PostgreSQL port (default: 5432)")
    parser.add_argument("--dbname", default=os.getenv("PGDATABASE", "postgres"), help="Database name (default: postgres)")
    parser.add_argument("--user", default=os.getenv("PGUSER", os.getenv("USER", "postgres")), help="PostgreSQL username")
    parser.add_argument("--password", default=os.getenv("PGPASSWORD"), help="PostgreSQL password")

    args = parser.parse_args()

    print(f"\n{BOLD}{GREEN}==========================================={RESET}")
    print(f"{BOLD}{GREEN}    PostgreSQL Table Viewer Application    {RESET}")
    print(f"{BOLD}{GREEN}==========================================={RESET}\n")

    host = args.host
    port = args.port
    dbname = args.dbname
    user = args.user
    password = args.password

    # Determine whether to run interactively
    # Run interactively if -i/--interactive flag is set or if no arguments were explicitly passed in TTY mode
    is_tty = sys.stdin.isatty()
    explicit_args_passed = any(arg in sys.argv for arg in ["--host", "--port", "--dbname", "--user", "--password"])
    
    if args.interactive or (is_tty and not explicit_args_passed and not os.getenv("PGPASSWORD")):
        host, port, dbname, user, password = prompt_interactive_credentials(
            default_host=host,
            default_port=port,
            default_dbname=dbname,
            default_user=user,
            default_password=password or ""
        )
    elif password is None and is_tty:
        password = getpass.getpass(prompt=f"Enter password for PostgreSQL user '{user}': ")

    print(f"{DIM}Connecting to PostgreSQL database:{RESET}")
    print(f"  • {BOLD}Host:{RESET}     {host}:{port}")
    print(f"  • {BOLD}Database:{RESET} {dbname}")
    print(f"  • {BOLD}User:{RESET}     {user}\n")

    driver, res = get_db_connection(host, port, dbname, user, password)

    if driver == "error":
        print(f"{BOLD}{RED}[-] Failed to connect to PostgreSQL database.{RESET}")
        print(f"{RED}Error Details:{RESET} {res}\n")
        print(f"{YELLOW}Troubleshooting Tips:{RESET}")
        print("  1. Verify PostgreSQL service is running: `sudo systemctl status postgresql`")
        print("  2. Check credentials (username, password, database name).")
        print("  3. Check host and port (default is localhost:5432).")
        print("  4. Ensure user permissions are set in `pg_hba.conf`.")
        sys.exit(1)

    print(f"{GREEN}[+] Successfully connected!{RESET} (Driver used: {BOLD}{driver}{RESET})\n")

    # Fetch tables
    if driver in ("psycopg2", "psycopg"):
        conn = res
        try:
            rows = query_tables_python(conn)
            conn.close()
        except Exception as e:
            print(f"{BOLD}{RED}[-] Failed to execute query:{RESET} {e}")
            sys.exit(1)
    elif driver == "psql":
        rows = parse_psql_output(res)

    if not rows:
        print(f"{YELLOW}[!] Connection successful, but no user tables were found in database '{dbname}'.{RESET}")
    else:
        print(f"{BOLD}{CYAN}Available Tables in '{dbname}':{RESET}")
        headers = ["Schema", "Table Name", "Type"]
        formatted_table = format_table(headers, rows)
        print(formatted_table)
        print(f"\n{BOLD}{GREEN}Total tables found: {len(rows)}{RESET}\n")

if __name__ == "__main__":
    main()

