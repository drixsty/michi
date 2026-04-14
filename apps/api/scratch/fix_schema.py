import json
import os

filepath = 'c:/Users/KevinTSAGUE/michi-app/backend/src/core/graphql/schema.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix login mutation
old_login = """                        organization=OrganizationType(
                            id=strawberry.ID(str(m.organization.id)),
                            name=m.organization.name,
                            slug=m.organization.slug,
                            plan=m.organization.plan,
                            subscription_status=m.organization.subscription_status,
                            created_at=m.organization.created_at
                        )"""
new_login = """                        organization=OrganizationType(
                            id=strawberry.ID(str(m.organization.id)),
                            name=m.organization.name,
                            slug=m.organization.slug,
                            plan=m.organization.plan,
                            subscription_status=m.organization.subscription_status,
                            created_at=m.organization.created_at,
                            settings=json.dumps(m.organization.settings or {})
                        )"""

# Fix switch_organization mutation
old_switch = """                        organization=OrganizationType(
                            id=strawberry.ID(str(m.organization.id)),
                            name=m.organization.name,
                            slug=m.organization.slug,
                            plan=m.organization.plan,
                            subscription_status=m.organization.subscription_status,
                            created_at=m.organization.created_at
                        )"""
new_switch = """                        organization=OrganizationType(
                            id=strawberry.ID(str(m.organization.id)),
                            name=m.organization.name,
                            slug=m.organization.slug,
                            plan=m.organization.plan,
                            subscription_status=m.organization.subscription_status,
                            created_at=m.organization.created_at,
                            settings=json.dumps(m.organization.settings or {})
                        )"""

# Replace both occurrences
# Since they are identical, we handle it carefully
if old_login in content:
    content = content.replace(old_login, new_login)
    print("Successfully replaced login/switch instances.")
else:
    print("Target content not found. Trying with CRLF/LF normalized search.")
    # Normalize line endings for the search
    norm_content = content.replace('\r\n', '\n')
    norm_old = old_login.replace('\r\n', '\n')
    norm_new = new_login.replace('\r\n', '\n')
    if norm_old in norm_content:
        norm_content = norm_content.replace(norm_old, norm_new)
        content = norm_content # Warning: this might change file encoding, but we save back as utf-8
        print("Successfully replaced normalized instances.")

with open(filepath, 'w', encoding='utf-8', newline='') as f:
    f.write(content)
