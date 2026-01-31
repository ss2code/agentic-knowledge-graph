import os
from dataclasses import dataclass

@dataclass
class Context:
    """
    Represents a specific Data/Graph Context.
    Allows the orchestrator to switch between different datasets and graph instances.
    """
    name: str
    base_path: str
    
    @property
    def data_dir(self):
        return os.path.join(self.base_path, 'user_data')
        
    @property
    def config_dir(self):
        return os.path.join(self.base_path, 'config')
        
    @property
    def output_dir(self):
        return os.path.join(self.base_path, 'output')
    
    @property
    def debug_dir(self):
        return os.path.join(self.base_path, 'debug')
        
    @property
    def neo4j_home(self):
        """Path to mount as /var/lib/neo4j involved in the docker container."""
        return os.path.join(self.base_path, 'neo4j_home')

    def ensure_directories(self):
        for d in [self.base_path, self.data_dir, self.config_dir, self.output_dir, self.neo4j_home, self.debug_dir]:
            os.makedirs(d, exist_ok=True)
            
    @staticmethod
    def from_path(path: str):
        """Creates a Context from a path. Name is the directory name."""
        abs_path = os.path.abspath(path)
        name = os.path.basename(abs_path)
        return Context(name=name, base_path=abs_path)
