"""
Script d'export du schéma GraphQL en format SDL (.graphql).
Utilisé par US 21.15 — Redirect output to file via Makefile.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.core.graphql.schema import schema
    # On utilise print pour permettre la redirection dans le Makefile
    print(str(schema))
except ImportError as e:
    print(f"Erreur d'import : {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Erreur lors de l'export : {e}", file=sys.stderr)
    sys.exit(1)
