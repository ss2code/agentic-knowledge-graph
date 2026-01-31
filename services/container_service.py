import subprocess
import time
import os
import sys

# Colors for CLI output
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

class ContainerService:
    def __init__(self, context):
        self.context = context
        self.container_name = f"neo4j-{context.name}" if context else "neo4j-default"

    def check_docker(self):
        """Checks if Docker is running."""
        try:
            subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except:
            return False

    def is_running(self):
        """Checks if our specific container is running."""
        # Check specifically for status='running'
        res = subprocess.run(
            ["docker", "ps", "--filter", f"name={self.container_name}", "--filter", "status=running", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        return self.container_name in res.stdout.strip()

    def exists(self):
        """Checks if container exists at all (stopped, created, exited)."""
        res = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        # Exact match to avoid substring issues (e.g. neo4j-data vs neo4j-data-2)
        return self.container_name in res.stdout.split()

    def stop_container(self):
        print(f"{YELLOW}Stopping container {self.container_name}...{RESET}")
        subprocess.run(["docker", "stop", self.container_name], stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "rm", self.container_name], stderr=subprocess.DEVNULL)

    def start_container(self, force_restart=False):
        if not self.check_docker():
            print(f"{RED}Error: Docker is not running or not installed.{RESET}")
            return False

        if self.exists():
            if force_restart:
                self.stop_container()
            else:
                if self.is_running():
                    print(f"{GREEN}Container {self.container_name} is already running.{RESET}")
                    return True
                else:
                    print(f"{YELLOW}Container {self.container_name} is stopped/created. Re-starting...{RESET}")
                    try:
                        subprocess.run(["docker", "start", self.container_name], check=True)
                        self.wait_for_healthy()
                        print(f"{GREEN}✅ Neo4j ({self.context.name}) is Online!{RESET}")
                        return True
                    except subprocess.CalledProcessError:
                        print(f"{YELLOW}Failed to restart. Forcing recreation...{RESET}")
                        self.stop_container()
        
        # If we reach here, we need to creating a new container
        print(f"{CYAN}Starting Neo4j for Context: {self.context.name}{RESET}")
        
        self.context.ensure_directories()
        
        import_vol = os.path.abspath(self.context.data_dir)
        data_vol = os.path.abspath(os.path.join(self.context.neo4j_home, 'data'))
        logs_vol = os.path.abspath(os.path.join(self.context.neo4j_home, 'logs'))
        
        os.makedirs(data_vol, exist_ok=True)
        os.makedirs(logs_vol, exist_ok=True)

        cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            "-p", "7474:7474", "-p", "7687:7687",
            "-e", "NEO4J_AUTH=neo4j/password",
            "-e", "NEO4J_PLUGINS=[\"apoc\"]",
            "-e", "NEO4J_apoc_export_file_enabled=true",
            "-e", "NEO4J_apoc_import_file_enabled=true",
            "-e", "NEO4J_apoc_import_file_use__neo4j__config=true",
            "-e", "NEO4J_dbms_security_procedures_unrestricted=apoc.*",
            "-v", f"{import_vol}:/var/lib/neo4j/import",
            "-v", f"{data_vol}:/data",
            "-v", f"{logs_vol}:/logs",
            "neo4j:latest"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"{YELLOW}Waiting for Neo4j to verify startup...{RESET}")
            self.wait_for_healthy()
            print(f"{GREEN}✅ Neo4j ({self.context.name}) is Online!{RESET}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{RED}Failed to start container: {e}{RESET}")
            return False

    def wait_for_healthy(self, timeout=30):
        # fast check loop
        for _ in range(timeout):
            try:
                 subprocess.run(
                    ["docker", "exec", self.container_name, "cypher-shell", 
                     "-u", "neo4j", "-p", "password", "RETURN 1"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                 )
                 return True
            except:
                time.sleep(1)
        print(f"{RED}Timeout waiting for Neo4j.{RESET}")
        return False
        
if __name__ == "__main__":
    from core.context import Context
    ctx = Context.from_path("tests/canned_data")
    svc = ContainerService(ctx)
    svc.start_container(force_restart=True)
