# JSON Preprocessor [![Build Status](https://travis-ci.org/tristanpenman/json-preprocessor.svg)](https://travis-ci.org/tristanpenman/json-preprocessor)

## Overview

This project provides a JSON Preprocessor library and command line utility that can be used to resolve JSON References and other preprocessor directives. It was originally motivated by the need to construct CloudFormation templates as part of a CI pipeline.

The following directives are supported:

* ```$exec```
* ```$join```
* ```$merge```
* ```$ref```

*Note that JSON Reference support is not yet complete.*

This project has been tested against Python 2.7 and 3.5.

## Directives

### $exec

The `$exec` directive allows the output of an external command to be included as a string value in a JSON document.

The command to be executed is provided as an array. The first element should be the path to an executable, with the remaining elements containing program arguments.

For example, take the following JSON snippet:

    {
        "timestamp": {
            "$exec": [ "/bin/date" ]
        }
    }

Resolving this directive would produce something like this:

    {
        "timestamp": "Thu 25 Sep 2014 15:30:40 AEST"
    }

It is important to note that an `$exec` directive is *not* executed in a shell, meaning that pipes, redirection and other shell built-ins are not available.

### $join

The input for a `$join` directive must be an array containing two elements. The first element is an array of strings (or directives that can be resolved to strings). The second element is a string that will be placed between adjacent elements in the output string.

Here is an example in which a `$join` directive is used to concatenate three string values:

    {
        "$join": [ ["A", "B", "C"], " " ]
    }

When resolved, this example would produce the following output:

    "A B C"

This can be useful when constructing strings using the output of other directives. Here is example that joins a static string with the output of an `$exec` directive:

    {
        "$join": [ [ "Current time:", { "$exec": [ "/bin/date" ] } ], " " ]
    }

This would be produce something like this:

    "Current time: Thu 25 Sep 2014 15:30:40 AEST"

Alternatively, an array delimiter can be used, which will change `$join` to perform array concatenation:

    {
        "$join": [
            [
                { "$ref": "file://abc.json" },
                [ "1", "2", "3" ],
                { "$ref": "file://xyz.json" }
            ],
            [ "*", "*" ]
        ]
    }

Assuming `abc.json` and `xyz.json` contain the arrays `["a", "b", "c"]` and `["x", "y", "z"]` respectively, the output would look like this:

    [ "a", "b", "c", "*", "*", "1", "2", "3", "*", "*", "x", "y", "z" ]

### $merge

The input for a `$merge` directive must be an array of objects. These objects will be combined, with the attributes of later objects taking precedence over those provided by earlier objects.

Here is an example of a `$merge` directive that combines two objects:

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

When resolved, this example `$merge` directive would produce the following output:

    {
        "my_attribute": "replacement_value",
        "another_attribute": "another_value"
    }

Note that the value of `my_attribute` defined by the first object has been replaced by the value defined by the second object.

### $ref

A `$ref` directive allows JSON References, and other remote resource references, to be resolved.

The JSON Preprocessor library has built-in support for the following resource types:

* `http://`
* `https://`
* `file://` (for absolute file references)
* `rel://` (for relative file references)

JSON References can be used to embed the all or part of an external JSON document in the preprocessor output. The library also allows custom resource types to be supported.

## JSON Preprocessor Utility

This project includes a JSON Preprocessor command line utility (see [json_preprocessor/cli.py](./json_preprocessor/cli.py)) that serves as an example of how to use the JSON Preprocessor library. It extends the `$ref` directive to retrieve attributes associated with CloudFormation resources, which can be useful when constructing CloudFormation templates as part of an automated build process.

### CFN References

This example registers a custom `$ref` URI type that adds support for CloudFormation resources via the [boto](https://github.com/boto/boto) library.

CloudFormation resources are identified using a specific URI format:

    cfn://<stack-name>[@region]/<logical-name>[/[attribute]]

`[]` denotes optional components, whereas `<>` denotes mandatory components.

If any mandatory components are missing, an exception will be raised.

If `[region]` is omitted, then the region will be determined using the current user's AWS credentials. If `[region]` is present, but not recognised by boto, an exception may be raised.

`[attribute]` may be any attribute that can be returned by the retrieval function. If `[attribute]` is omitted, the 'PhysicalResourceID' attribute will be returned.

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

If the installation was successful, usage instructions for `json-preprocessor` will be displayed.

## Development

The json_preprocessor module also includes a `__main__.py` file, so an alternative is to run the example locally:

    pip install -r requirements
    python -m json_preprocessor

And to run the tests:

    python -m unittest

## License

This code is licensed under the 3-clause BSD License.

See the LICENSE file for more information.

## Acknowledgements

Shout-out to [elruwen](https://github.com/elruwen) for early code reviews.
