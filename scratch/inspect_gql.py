import asyncio
import sys
import os

# Ajouter le chemin src pour les imports
sys.path.append(os.path.join(os.getcwd(), "apps", "api", "src"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "apps", "api", ".env"))

from core.graphql.schema import schema

def inspect_schema():
    # On inspecte le type Query
    query_type = schema.get_type_by_name("Query")
    print("--- Fields in Root Query ---")
    for field in query_type.fields:
        print(f"- {field.name}")
        
    org_type = schema.get_type_by_name("OrganizationType")
    print("\n--- Fields in OrganizationType ---")
    for field in org_type.fields:
        print(f"- {field.name}")
        
    member_type = schema.get_type_by_name("OrganizationMemberType")
    print("\n--- Fields in OrganizationMemberType ---")
    for field in member_type.fields:
        print(f"- {field.name}")

    user_type = schema.get_type_by_name("UserType")
    print("\n--- Fields in UserType ---")
    for field in user_type.fields:
        print(f"- {field.name}")

if __name__ == "__main__":
    inspect_schema()
