# JSON Preprocessor [![Build Status](https://travis-ci.org/tristanpenman/json-preprocessor.svg)](https://travis-ci.org/tristanpenman/json-preprocessor)

## Overview

This project provides a JSON Preprocessor library and command line utility that
can be used to resolve JSON References and other pre-processor directives. It
was originally motivated by the need to construct CloudFormation templates as
part of a CI pipeline.

The following pre-processor directives are supported:

* ```$exec```
* ```$join```
* ```$merge```
* ```$ref```

*Note that JSON Reference support is not yet complete.*

This project has been tested against Python 2.7 and 3.5.

## Directives

### $exec

An $exec directive allows the output of an external command to be used as a
value in a JSON document.

The command to be executed is provided as an array. The first element should
be the path to an executable, with the remaining elements containing program
arguments.

For example, the following JSON snippet:

    {
        "timestamp": {
            "$exec": [ "/bin/date" ]
        }
    }

would produce output similar to:

    {
        "timestamp": "Thu 25 Sep 2014 15:30:40 AEST"
    }

Note that an $exec directive is *not* executed in a shell, which means that
functionality such as pipes and shell built-ins are not available.

### $join

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

This can be useful when constructing strings using the resolved values of
other directives. For example:

    {
        "$join": [ " ", [ "Current time:", { "$exec": [ "/bin/date" ] } ] ]
    }

### $merge

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


### $ref

A $ref allows JSON References, and other remote resource references, to be
resolved.

The JSON Preprocessor library supports the following URIs:

* ```http://```
* ```https://```
* ```file://``` (for absolute file references)
* ```rel://``` (for relative file references)

## JSON Preprocessor Utility

This project includes a JSON Preprocessor command line utility that serves as
an example of how to use the JSON Preprocessor library. It extends the $ref
directive to retrieve attributes associated with CloudFormation resources,
which can be useful when constructing CloudFormation templates as part of an
automated build process.

### CFN References

This example registers a custom ```$ref``` URI type that adds support for
CloudFormation resources via the [boto](https://github.com/boto/boto) library.

CloudFormation resources are identified using a specific URI format:

    cfn://<stack-name>[@region]/<logical-name>[/[attribute]]

```[]``` denotes optional components, whereas ```<>``` denotes mandatory
components.

If any mandatory components are missing, an exception will be raised.

If ```[region]``` is omitted, then the region will be determined using the
current user's AWS credentials. If ```[region]``` is present, but not
recognised by boto, an exception may be raised.

```[attribute]``` may be any attribute that can be returned by the retrieval
function. If ```[attribute]``` is omitted, the 'PhysicalResourceID' attribute
will be returned.

### Usage

    Usage: json-preprocessor [OPTIONS] <path-to-document> COMMAND [ARGS]...

      Resolve a CloudFormation template containing JSON pre-processor
      directives.

    Options:
      --minify                 Compact the JSON output by removing whitespace.
      --output-file <path>     Optional path to which JSON output will be written.
                               By default output will be written to STDOUT.
      --parameter <key=value>  A key-value pair to be passed to the template; this
                               option may be used more than once to pass in
                               multiple key-value pairs.
      --help                   Show this message and exit.

## Installation

Both the library and an example command line utility can be installed using pip:

    pip install -r requirements
    pip install .

You can check that the installation was successful by running the command line
utility with no arguments:

    json-preprocessor

If the installation was successful, usage instructions for `json-preprocessor`
will be displayed.

## License

This code is licensed under the 3-clause BSD License.

See the LICENSE file for more information.

## Acknowledgements

Shout-out to [elruwen](https://github.com/elruwen) for early code reviews.
