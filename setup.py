import re
from setuptools import setup


with open('requirements.txt', 'r') as requirements_file:
    requirements = requirements_file.read().splitlines()


with open('asyncify/__init__.py', 'r') as version_file:
    version = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', version_file.read(), re.MULTILINE).group(1)  # type: ignore


with open('README.rst', 'r') as rm:
    readme = rm.read()


# fmt: off
packages = [
    'asyncify'
    ]


extras_require = {
    'docs': [
        'sphinx-press-theme'
        ]
    }
# fmt: on

setup(
    name='asyncify-python',
    author='The Master',
    version=version,
    packages=packages,
    license='MIT',
    description='A python library to make things async!',
    project_urls={
        'GitHub': 'https://github.com/TheMaster3558/asyncify',
        'Documentation': 'https://asyncify.readthedocs.io/en/latest',
    },
    long_description=readme,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    install_requires=requirements,
    extras_require=extras_require,
    python_requires='>=3.7.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Typing :: Typed',
    ],
)
