import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from core.database.models import SupportAuditLog
import uuid

@pytest.fixture(autouse=True)
async def setup_triggers(db_session):
    # Applique les triggers SQLite sur la base de test en mémoire
    await db_session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS prevent_update_audit_logs
        BEFORE UPDATE ON support_audit_logs
        BEGIN
            SELECT RAISE(FAIL, 'Updates not allowed on support_audit_logs');
        END;
    """))
    await db_session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS prevent_delete_audit_logs
        BEFORE DELETE ON support_audit_logs
        BEGIN
            SELECT RAISE(FAIL, 'Deletes not allowed on support_audit_logs');
        END;
    """))
    await db_session.commit()


async def test_audit_log_creation_and_immutability(db_session, test_user):
    # 1. Crée un log d'audit
    org_id = test_user.current_organization_id
    assert org_id is not None
    
    log_id = uuid.uuid4()
    audit_log = SupportAuditLog(
        id=log_id,
        support_user_id=test_user.id,
        impersonated_org_id=org_id,
        action="Test action",
        flow_id="test-flow-id"
    )
    
    db_session.add(audit_log)
    await db_session.commit()
    
    # 2. Tente de modifier le log
    # On recharge l'objet dans la session
    await db_session.execute(text("select 1")) # Refresh session state
    audit_log.action = "Modified action"
    
    # La mise à jour doit lever une erreur opérationnelle de trigger
    with pytest.raises((OperationalError, IntegrityError)) as exc_info:
        await db_session.commit()
    
    assert "Updates not allowed" in str(exc_info.value)
    await db_session.rollback()
    
    # 3. Tente de supprimer le log
    # On s'assure qu'on travaille sur une session propre
    audit_log_to_delete = await db_session.get(SupportAuditLog, log_id)
    assert audit_log_to_delete is not None
    
    await db_session.delete(audit_log_to_delete)
    
    # La suppression doit lever une erreur opérationnelle de trigger
    with pytest.raises((OperationalError, IntegrityError)) as exc_info:
        await db_session.commit()
        
    assert "Deletes not allowed" in str(exc_info.value)
    await db_session.rollback()
