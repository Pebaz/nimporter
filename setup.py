import io
from setuptools import setup

setup(
    name='nimporter',
    version='2.0.0',
    license='MIT',
    description='Compile Nim extensions for Python when imported!',
    long_description=io.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='http://github.com/Pebaz',
    url='http://github.com/Pebaz/Nimporter',
    packages=['nimporter'],
    install_requires=[
        'py-cpuinfo>=8.0.0',  # Auto-detect user architecture
        'icecream>=2.1.2',  # Instrumentation
        'cookiecutter>=1.7.3'  # Project template
    ],
    entry_points={
        'console_scripts' : [
            'nimporter=nimporter.cli:main'
        ]
    }
)
