import json
import subprocess
import itertools

from typing import Union, Callable, Optional, Dict
from urllib.parse import urldefrag, urlsplit
from urllib.request import urlopen

Node = Union[list, dict]


def resolve_exec(node: Node, base_resolver_fn: Callable) -> str:
    """ Resolve an $exec pre-processor directive.
    """
    if not isinstance(node, list):
        raise Exception("$exec value must be an array")
    elif len(node) < 1:
        raise Exception("$exec array must contain at least one element")

    # Resolve each object in the array
    args = [base_resolver_fn(value, base_resolver_fn) for value in node]

    process_output = subprocess.check_output(args, shell=False)
    return process_output.decode("utf-8").rstrip('\n')


def resolve_join(node: Node, base_resolver_fn: Callable) -> str:
    """ Resolve a $join pre-processor directive.

        The value of $join pre-processor directive must be an array containing
        two elements. The first element is an array of strings, or objects
        that can be resolved to strings. The second element is a string that
        will be placed between adjacent elements in the output string.

        The second argument is optional.

        An example $join pre-preprocessor directive could take the following
        form:

            {
                "$join": [ " ", ["A", "B", "C"] ]
            }

        When resolved, this example $join directive would produce the
        following output:

            "A B C"

        Alternatively, an array delimiter may be provided, in which case
        this directive will perform an array join.
    """

    # Check that the value of the $join directive is an array containing
    # exactly two elements
    if not isinstance(node, list):
        raise Exception("$join value must be an array")
    elif len(node) == 0 or len(node) > 2:
        raise Exception("$join array may only provide elements and a delimiter")

    # Handle array concatenation
    delimiter = node[1]
    if delimiter is None:
        delimiter = ''
    elif isinstance(delimiter, list):
        lists = []
        for element in node[0]:
            resolved = base_resolver_fn(element, base_resolver_fn)
            if not isinstance(resolved, list):
                raise Exception("$join with array delimiter can only join other arrays")
            lists.append(resolved)
            lists.append(delimiter)
        lists.pop()
        return list(itertools.chain.from_iterable(lists))

    # Resolve and join each element
    return delimiter.join([base_resolver_fn(element, base_resolver_fn)
                          for element in node[0]])


def resolve_merge(node: Node, base_resolver_fn: Callable) -> dict:
    """ Resolve a $merge pre-processor directive.

        The value of a $merge directive must be an array of objects. These
        objects will be combined, with the attributes of later objects taking
        precedence over those provided by earlier objects.

        An example $merge pre-preprocessor directive could take the following
        form:

            {
                "$merge": [
                    {
                        "my_attribute": "original_value",
                        "another_attribute": "another_value"
                    },
                    {
                        "my_attribute": "replacement_value"
                    }
                ]
            }

        When resolved, this example $merge directive would produce the
        following output:

            {
                "my_attribute": "replacement_value",
                "another_attribute": "another_value"
            }

        Note that the value of 'my_attribute' defined by the first object in
        the array has been replaced by the value defined by the second object.
    """

    # Check that the value of the $merge directive is an array
    if not isinstance(node, list):
        raise Exception("merge value must be an array")

    # Resolve each object in the array
    values = [base_resolver_fn(value, base_resolver_fn) for value in node]

    # Merge each object into the result
    result = dict()
    for value in values:
        if not isinstance(value, dict):
            raise Exception("merge operand must be an object")
        result.update(value)
    return dict(result)


def resolve_ref(node: Node, base_resolver_fn: Callable, uri_handlers: Dict[str, Callable]):
    ref = base_resolver_fn(node, base_resolver_fn)
    base_uri, frag = urldefrag(ref)
    base_uri_parts = urlsplit(base_uri)

    # Check for a custom URI handler that supports the current scheme
    try:
        items = uri_handlers.iteritems()
    except AttributeError:
        items = uri_handlers.items()
    for key, handler_fn in items:
        if base_uri_parts.scheme == key:
            return base_resolver_fn(handler_fn(ref), base_resolver_fn)

    # Use the default urllib2 functionality to parse the URI
    return base_resolver_fn(json.loads(urlopen(base_uri).read()),
                            base_resolver_fn)


def resolve_node(node: Union[list, dict], doc_args: dict, custom_uri_handlers: dict) -> Node:

    def resolve_uri_arg(uri: str):
        base_uri, frag = urldefrag(uri)
        base_uri_parts = urlsplit(base_uri)
        if base_uri_parts.netloc not in doc_args:
            raise Exception("Argument '" + base_uri_parts.netloc + "' not set.")
        return doc_args[base_uri_parts.netloc]

    def resolve_uri_rel(uri: str):
        base_uri, frag = urldefrag(uri)
        base_uri_parts = urlsplit(base_uri)
        with open(base_uri_parts.netloc + base_uri_parts.path) as data:
            if base_uri_parts.query:
                query_args = dict(arg.split("=")
                                  for arg in base_uri_parts.query.split("&"))
            else:
                query_args = dict()
            new_dict = doc_args.copy()
            new_dict.update(query_args)
            return resolve_node(json.load(data), new_dict, custom_uri_handlers)

    default_uri_handlers = {
        'arg': resolve_uri_arg,
        'rel': resolve_uri_rel
    }

    def resolve_ref_with_uri_handlers(inner_node: str, inner_base_resolver_fn: Callable):
        new_dict = default_uri_handlers.copy()
        new_dict.update(custom_uri_handlers)
        return resolve_ref(inner_node, inner_base_resolver_fn, new_dict)

    resolvers = {
        '$ref': resolve_ref_with_uri_handlers,
        '$join': resolve_join,
        '$merge': resolve_merge,
        '$exec': resolve_exec
    }

    def base_resolver_fn(inner_node, inner_base_resolver_fn):
        del inner_base_resolver_fn
        return resolve_node(inner_node, doc_args, custom_uri_handlers)

    if isinstance(node, list):
        # Resolve each element in an array
        return [base_resolver_fn(value, base_resolver_fn) for value in node]

    elif isinstance(node, dict):
        # Check for a matching custom resolver for an object
        for key, custom_resolver_fn in resolvers.items():
            if key in node:
                return custom_resolver_fn(node[key], base_resolver_fn)

        # Resolve the value of each attribute in an object
        return {attr: base_resolver_fn(value, base_resolver_fn)
                for attr, value in node.items()}

    return node


def resolve(node: Node, doc_args: dict, custom_uri_handlers: Optional[dict] = None) -> Node:
    """Recursively resolve nodes in a JSON tree
    """
    if not custom_uri_handlers:
        custom_uri_handlers = dict()

    return resolve_node(node, doc_args, custom_uri_handlers)
