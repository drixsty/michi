import pytest
import json

@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyze_csv_mutation(client, auth_token):
    query = """
        mutation AnalyzeCsv($csvContent: String!) {
            analyzeCsv(csvContent: $csvContent) {
                columns
                suggestedMapping {
                    targetField
                    csvColumn
                }
                anomalies
            }
        }
    """
    
    csv_content = "Ref,Nom,Stock\nPROD1,Produit 1,-10"
    
    response = await client.post(
        "/graphql",
        json={
            "query": query,
            "variables": {"csvContent": csv_content}
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    analysis = data["data"]["analyzeCsv"]
    assert "Ref" in analysis["columns"]
    assert any(s["targetField"] == "sku" and s["csvColumn"] == "Ref" for s in analysis["suggestedMapping"])
    
    # Vérifier les anomalies
    anomalies = json.loads(analysis["anomalies"])
    assert len(anomalies) > 0
    assert anomalies[0]["errors"]["Stock"] == "NEGATIVE_VALUE"

@pytest.mark.asyncio
@pytest.mark.integration
async def test_smart_import_mutation(client, auth_token, test_organization):
    # D'abord on récupère un store_id (ou on en crée un via mutation si nécessaire)
    # Pour le test on suppose qu'il y a un store par défaut ou on utilise l'ID de l'organisation
    
    # On commence par lister les sources pour avoir un ID
    sources_query = "query { sources { id } }"
    src_res = await client.post("/graphql", json={"query": sources_query}, headers={"Authorization": f"Bearer {auth_token}"})
    store_id = src_res.json()["data"]["sources"][0]["id"]

    mutation = """
        mutation SmartImport($input: SmartImportInput!) {
            smartImport(input: $input) {
                success
                message
                productsCount
            }
        }
    """
    
    csv_content = "sku,title,stock\nTEST-IMPORT,Produit Importé,15"
    mapping = {"sku": "sku", "title": "title", "stock": "stock"}
    
    response = await client.post(
        "/graphql",
        json={
            "query": mutation,
            "variables": {
                "input": {
                    "storeId": store_id,
                    "csvContent": csv_content,
                    "mapping": json.dumps(mapping)
                }
            }
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["data"]["smartImport"]["success"] is True
    assert res_data["data"]["smartImport"]["productsCount"] == 1
