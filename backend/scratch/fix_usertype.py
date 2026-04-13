import os

filepath = 'c:/Users/KevinTSAGUE/michi-app/backend/src/core/graphql/schema.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We look for UserType(...) calls and add email=...
# This is a bit tricky with regex, so we'll do specific replacements for known blocks.

# 1. me resolve
old_me = """        return UserType(
            id=strawberry.ID(str(user.id)),
            first_name=user.first_name,
            last_name=user.last_name,"""
new_me = """        return UserType(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,"""

# 2. update_profile
old_up = """        return UserType(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            current_organization_id=strawberry.ID(str(user.current_organization_id)) if user.current_organization_id else None,"""
# (wait, update_profile already has email=user.email? Let's check)

# 3. login / switch_org / register / googleLogin
# These often use user.email or user_schema.email

def fix_usertype(cnt):
    # Fix 'me'
    cnt = cnt.replace(old_me, new_me)
    
    # Fix 'update_profile' actually HAS email according to my previous view_file (line 325)
    
    # Let's just do a generic sweep if any UserType( is missing email=
    return cnt

# I'll just manual replace the ones I know are missing.
# Checking login mutation (line 215 in previous view)
old_login = """        return AuthPayload(
            token=result.token,
            user=UserType(
                id=strawberry.ID(str(user.id)),
                email=user.email,"""
# (wait, login might already have it? Let's check view_file 190-250)

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if "return UserType(" in line or "user=UserType(" in line:
        # Check if next few lines contain email=
        has_email = False
        for j in range(i+1, min(i+10, len(lines))):
            if "email=" in lines[j]:
                has_email = True
                break
        if not has_email:
            print(f"Adding email to UserType at line {i+1}")
            # We assume 'user' or 'user_schema' is available. 
            # In 'me' it's 'user'. In 'switch_organization' it's 'user_schema'.
            # We need to be careful.
            pass

# Actually, I'll just use simple string replacements for the ones I've verified are broken.

final_content = content.replace(old_me, new_me)

with open(filepath, 'w', encoding='utf-8', newline='') as f:
    f.write(final_content)
