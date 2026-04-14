import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.graphql.schema import schema

def export_schema():
    target_path = Path(__file__).parent.parent.parent.parent / "docs-site" / "static" / "schema.graphql"
    print(f"Exporting schema to {target_path}...")
    
    sdl = schema.as_str()
    
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(sdl)
    
    print("Done.")

if __name__ == "__main__":
    export_schema()
