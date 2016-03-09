#!/usr/bin/env python
import json
import subprocess

try:
    from urlparse import urldefrag, urlsplit
except ImportError:
    from urllib.parse import urldefrag, urlsplit

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


def resolve_exec(node, base_resolver_fn):
    """ Resolve an $exec pre-processor directive.
    """
    process_output = subprocess.check_output(
        base_resolver_fn(node, base_resolver_fn), shell=False)
    try:
        return unicode(process_output).rstrip('\n')
    except NameError as e:
        return process_output.decode("utf-8").rstrip('\n')


def resolve_join(node, base_resolver_fn):
    """ Resolve a $join pre-processor directive.

        The value of $join pre-processor directive must be an array containing
        two elements. The first element is a string that will be placed between
        adjacent elements in the output string. The second element is an array
        of strings, or objects that can be resolved to strings.

        An example $join pre-preprocessor directive could take the following
        form:

            {
                "$join": [ " ", ["A", "B", "C"] ]
            }

        When resolved, this example $join directive would produce the
        following output:

            "A B C"
    """

    # Check that the value of the $join directive is an array containing
    # exactly two elements
    if not isinstance(node, list):
        raise Exception("$join value must be an array")
    elif len(node) != 2:
        raise Exception("$join array must provide separator and elements")

    # Resolve and join each element
    return node[0].join([base_resolver_fn(element, base_resolver_fn)
                         for element in node[1]])


def resolve_merge(node, base_resolver_fn):
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


def resolve_ref(node, base_resolver_fn, uri_handlers):
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


def resolve_node(node, doc_args, custom_uri_handlers):

    def resolve_uri_arg(uri):
        base_uri, frag = urldefrag(uri)
        base_uri_parts = urlsplit(base_uri)
        if base_uri_parts.netloc not in doc_args:
            raise Exception("Argument '" + base_uri_parts.netloc + "' not set.")
        return doc_args[base_uri_parts.netloc]

    def resolve_uri_rel(uri):
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

    def resolve_ref_with_uri_handlers(inner_node, inner_base_resolver_fn):
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
        try:
            items = resolvers.iteritems()
        except AttributeError:
            items = resolvers.items()
        for key, custom_resolver_fn in items:
            if key in node:
                return custom_resolver_fn(node[key], base_resolver_fn)

        # Resolve the value of each attribute in an object
        return {attr: base_resolver_fn(value, base_resolver_fn)
                for attr, value in node.items()}

    return node


def resolve(node, doc_args, custom_uri_handlers=None):
    """Recursively resolve nodes in a JSON tree
    """
    if not custom_uri_handlers:
        custom_uri_handlers = dict()

    return resolve_node(node, doc_args, custom_uri_handlers)
