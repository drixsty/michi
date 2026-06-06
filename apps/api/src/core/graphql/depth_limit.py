from strawberry.extensions import SchemaExtension
from graphql import (
    GraphQLError,
    FieldNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    OperationDefinitionNode,
    FragmentDefinitionNode,
    SelectionSetNode,
)

class DepthLimitExtension(SchemaExtension):
    """
    GraphQL Query Depth Limiting Extension.
    Prevents Denial of Service (DoS) attacks from excessively nested queries.
    """
    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        super().__init__()

    def on_validate(self):
        execution_context = self.execution_context
        document = execution_context.graphql_document
        
        if document:
            fragments = {
                definition.name.value: definition
                for definition in document.definitions
                if isinstance(definition, FragmentDefinitionNode)
            }
            
            def get_depth(node, fragments_dict) -> int:
                if isinstance(node, FieldNode):
                    if node.name.value.startswith('__'):
                        return 0
                    if not node.selection_set:
                        return 1
                    return 1 + max((get_depth(selection, fragments_dict) for selection in node.selection_set.selections), default=0)
                
                elif isinstance(node, SelectionSetNode):
                    return max((get_depth(selection, fragments_dict) for selection in node.selections), default=0)
                    
                elif isinstance(node, FragmentSpreadNode):
                    fragment = fragments_dict.get(node.name.value)
                    if fragment:
                        return get_depth(fragment.selection_set, fragments_dict)
                    return 0
                    
                elif isinstance(node, (InlineFragmentNode, OperationDefinitionNode, FragmentDefinitionNode)):
                    if not node.selection_set:
                        return 0
                    return max((get_depth(selection, fragments_dict) for selection in node.selection_set.selections), default=0)
                    
                return 0

            for definition in document.definitions:
                if isinstance(definition, OperationDefinitionNode):
                    depth = get_depth(definition, fragments)
                    if depth > self.max_depth:
                        raise GraphQLError(
                            f"GraphQL query depth limit of {self.max_depth} exceeded. Query depth was {depth}."
                        )
        yield
