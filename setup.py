from distutils.core import setup

setup(
    name='JSON Preprocessor',
    packages=['json_preprocessor'],
    scripts=['bin/json-preprocessor'],
    description='JSON Preprocessor library and command line utility that can '
                'be used to resolve JSON References and other pre-processor '
                'directives.',
    requires=['boto', 'click']
)
