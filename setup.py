from distutils.core import setup

setup(
    name='JSON Preprocessor',
    packages=['json_preprocessor'],
    url='https://github.com/tristanpenman/json-preprocessor',
    description='JSON Preprocessor library and command line utility that can '
                'be used to resolve JSON References and other pre-processor '
                'directives.',
    entry_points = {
        'console_scripts': ['json-preprocessor = json_preprocessor.cli:run']
    },
    requires=['boto', 'click']
)
