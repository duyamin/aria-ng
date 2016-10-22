from aria import install_aria_extensions
from aria.consumption import ConsumptionContext, ConsumerChain, Read, Validate, Model, Instance
from aria.loading import LiteralLocation

install_aria_extensions()

def parse_text(payload, file_search_paths=[]):
    context = ConsumptionContext()
    context.presentation.location = LiteralLocation(payload)
    context.loading.file_search_paths += file_search_paths
    ConsumerChain(context, (Read, Validate, Model, Instance)).consume()
    if not context.validation.dump_issues():
        return context.modeling.instance
    return None

print parse_text("""
tosca_definitions_version: tosca_simple_yaml_1_0
topology_template:
  node_templates:
    MyNode:
      type: tosca.nodes.Compute 
""")
