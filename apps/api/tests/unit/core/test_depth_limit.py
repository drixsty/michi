import pytest
from core.graphql.schema import schema

@pytest.mark.asyncio
async def test_depth_limit_ok():
    # Shallow query (introspection + simple structure)
    query = """
    query {
        __schema {
            queryType {
                name
            }
        }
    }
    """
    result = await schema.execute(query)
    # Introspection might have no errors
    assert result.errors is None

@pytest.mark.asyncio
async def test_depth_limit_exceeded():
    # Deeply nested query (depth of 7)
    query = """
    query {
        organizations {
            stores {
                products {
                    supplier {
                        store {
                            name
                        }
                    }
                }
            }
        }
    }
    """
    result = await schema.execute(query)
    assert result.errors is not None
    
    error_messages = [error.message for error in result.errors]
    assert any("GraphQL query depth limit of 5 exceeded" in msg for msg in error_messages)
