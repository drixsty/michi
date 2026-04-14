import os
import sys

# Ajouter le chemin du projet
sys.path.append(os.getcwd())

from src.core.graphql.schema import schema

# Inspecter le type Mutation
mutation_type = schema.get_type_by_name("Mutation")
if mutation_type:
    print(f"Mutations found: {[f.name for f in mutation_type.fields]}")
else:
    print("Mutation type NOT FOUND in schema")

# Inspecter le type Query
query_type = schema.get_type_by_name("Query")
if query_type:
    print(f"Queries found: {[f.name for f in query_type.fields]}")
else:
    print("Query type NOT FOUND in schema")
