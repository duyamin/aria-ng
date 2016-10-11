ARIA
====

ARIA is a platform and a set of tools for building TOSCA-based products, such as orchestrators.
Its features can be accessed via a well-documented Python API, as well as a language-agnostic
RESTful API that can be deployed as a microservice.

On its own, ARIA provides built-in tools for blueprint validation and for creating ready-to-run
service instances. 

ARIA adheres strictly and meticulously to the
[TOSCA Simple Profile v1.0 specification](http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/csprd02/TOSCA-Simple-Profile-YAML-v1.0-csprd02.html),
providing state-of-the-art validation at seven different levels:

0. Platform errors. E.g. network, hardware, or even an internal bug in ARIA (let us know,
   please!).
1. Syntax and format errors. E.g. non-compliant YAML, XML, JSON.
2. Field validation. E.g. assigning a string where an integer is expected, using a list
   instead of a dict.
3. Relationships between fields within a type. This is "grammar" as it applies to rules for
   setting the values of fields in relation to each other.
4. Relationships between types. E.g. referring to an unknown type, causing a type inheritance
   loop. 
5. Topology. These errors happen if requirements and capabilities cannot be matched in order
   to assemble a valid topology.
6. External dependencies. These errors happen if requirement/capability matching fails due to
   external resources missing, e.g. the lack of a valid virtual machine, API credentials, etc. 

Validation errors include a plain English message and when relevant the exact location (file,
row, column) of the data the caused the error.

The ARIA API documentation always links to the relevant section of the specification, and
likewise we provide an annotated version of the specification that links back to the API
documentation.


Quick Start
-----------

You need Python v2.7. Python v3 is not currently supported. Use a [virtualenv](https://virtualenv.pypa.io/en/stable/):

	pip install virtualenv
	virtualenv env
	. env/bin/activate
	pip install .

Now create a service instance from a TOSCA blueprint:

	aria blueprints/tosca/node-cellar/node-cellar.yaml
	
You can also get it in JSON or YAML formats:

	aria blueprints/tosca/node-cellar/node-cellar.yaml --json

Or get an overview of the relationship graph:

	aria blueprints/tosca/node-cellar/node-cellar.yaml --graph

You can provide inputs as JSON, overriding default values provided in the blueprint

	aria blueprints/tosca/node-cellar/node-cellar.yaml --inputs='{"openstack_credential": {"user": "username"}}'

Instead of providing them explicitly, you can also provide them in a file or URL, in either
JSON or YAML. If you do so, the value must end in ".json" or ".yaml":

	aria blueprints/tosca/node-cellar/node-cellar.yaml --inputs=blueprints/tosca/inputs.yaml


API Architecture
----------------

ARIA's parsing engine comprises individual "consumers" (in the `aria.consumption`
package) that do things with blueprints. When chained together, each performs a
different task, adds its own validations, and can provide its own output.

Parsing happens in five phases, represented in five packages:

* `aria.loading`: Loaders are used to read the TOSCA data, usually as text.
  For example UriTextLoader will load text from URIs (including files).
* `aria.reading`: Readers convert data from the loaders into agnostic raw
  data. For example, `YamlReader` converts YAML text into Python dicts, lists,
  and primitives.
* `aria.presentation`: Presenters wrap the agnostic raw data in a nice
  Python facade (a "presentation") that makes it much easier to work with the data,
  including utilities for validation, querying, etc. Note that presenters are
  _wrappers_: the agnostic raw data is always maintained intact, and can always be
  accessed directly or written back to files. Importantly, even YAML comments are
  maintained. So, you can modify the presentation and write it back to a YAML file
  while keeping all the original YAML comments in the file in their right places.
* `aria.modeling.model`: Here the topology is normalized into a coherent
  structure of node templates, requirements, and capabilities. Types are inherited
  and properties are assigned. The service model is a _new_ structure,
  which is not mapped to the YAML. In fact, it is possible to generate the model
  programmatically, or from a DSL parser other than TOSCA.
* `aria.modeling.instance`: The service instance is an instantiated service
  model. Node templates turn into node instances (with unique IDs), and requirements
  are satisfied by matching them to capabilities. This is where level 5 validation
  errors are detected (see above).

The phases do not have to be used in order. Indeed, consumers do not have to be
used at all: ARIA can be used to _produce_ blueprints. For example, it is possible
to fill in the `aria.presentation` classes programmatically, in Python, and then
write the presentation to a YAML file as compliant TOSCA. The same technique can be
used to convert from one DSL (consume it) to another (write it).

The term "agnostic raw data" (ARD?) appears often in the documentation. It denotes
data structures comprising _only_ Python dicts, lists, and primitives, such that
they can always be converted to and from language-agnostic formats such as YAML,
JSON, and XML. A considerable effort has been made to conserve the agnostic raw
data at all times. Thus, though ARIA makes good use of the dynamic power of Python,
you will _always_ be able to use ARIA with other systems.


CLI Tool
--------

Though ARIA is fully exposed as an API, it also comes with a CLI tool to allow you to
work from the shell:

	aria blueprints/tosca/node-cellar/node-cellar.yaml instance

The CLI supports the following commands to create variations of the default consumer
chain:

* `presentation`: emits a colorized textual representation of the Python presentation
   classes wrapping the blueprint.
* `model`: emits a colorized textual representation of the complete service model derived
   from the validated blueprint. This includes all the node templates, with their
   requirements satisfied at the level of relating to other node templates. Use `--types`
   to see just the type hierarchy.
* `instance`: **this is the default command**; emits a colorized textual representation of
   a service instance instantiated from the service model. Here the node templates
   are each used to create one or more nodes, with the appropriate relationships between
   them. Note that every time you run this consumer, you will get a different set of node
   IDs. Use `--graph` to see just the node relationship graph.
   
For all these commands, you can also use `--json` or `--yaml` flags to emit in those
formats.

Additionally, The CLI tool lets you specify the complete classname of your own custom
consumer to chain at the end of the default consumer chain, after `instance`.

Your customer consumer can be an entry point into a powerful TOSCA-based tool or
application, such as an orchestrator, a graphical modeling tool, etc.


REST Tool
---------

The ARIA REST tool starts a RESTful HTTP server that can do basic validation over the
wire:

    aria-rest

With the server started, you can hit a few endpoints:

    curl http://localhost:8204/openoapi/tosca/v1/instance/blueprints/tosca/node-cellar/node-cellar.yaml
    
    curl http://localhost:8204/openoapi/tosca/v1/validate/blueprints/tosca/node-cellar/node-cellar.yaml

You will get a JSON response with a service instance or validation issues.

You can send inputs:

	curl http://localhost:8204/openoapi/tosca/v1/instance/blueprints/tosca/node-cellar/node-cellar.yaml?inputs=%7B%22openstack_credential%22%3A%7B%22user%22%3A%22username%22%7D%7D

	curl http://localhost:8204/openoapi/tosca/v1/instance/blueprints/tosca/node-cellar/node-cellar.yaml?inputs=blueprints/tosca/inputs.yaml

You can also POST a blueprint over the wire:

    curl --data-binary @blueprints/tosca/node-cellar/node-cellar.yaml http://localhost:8204/openoapi/tosca/v1/instance

If you POST and also want to import from the filesystem, note that you must specify search
paths when you start the server:

    aria-rest --path blueprints/tosca /another/path/to/imports


Generator (Extension)
---------------------

This converts the blueprint into Python code: a bunch of Python classes representing
the blueprint. Thus, node types become classes, the instances being nodes, interfaces
can be turned into methods, and these are connected to each other via special
relationship classes. You can use these classes directly in your product, allowing
a quick and easy way to move from a TOSCA blueprint to executable code.

Note that the generator is entirely optional: it is very much possible to consume
the service instance without converting it into Python code.


Development
-----------

You do not want to install with `pip`, but instead work directly with the source files:

	pip install virtualenv
	virtualenv env
	. env/bin/activate
	make requirements

You can then run the scripts in the main directory:

	./aria blueprints/tosca/node-cellar/node-cellar.yaml
    ./aria-rest

To run tests:

	make

To build the documentation:

	make docs

Here's a quick example of using the API to parse a given string:

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
