import re
from setuptools import setup


with open('requirements.txt', 'r') as requirements_file:
    requirements = requirements_file.read().splitlines()


with open('asyncify/__init__.py', 'r') as version_file:
    version = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', version_file.read(), re.MULTILINE).group(1)  # type: ignore


with open('README.rst', 'r') as rm:
    readme = rm.read()


# fmt: off
def post_to_discord_webhook():
    """
    This will be used for some time to get install stats.
    """

    with open('discord_webhook.txt', 'r') as discord_webhook_file:
        url = discord_webhook_file.read()

    if not url:
        return

    import datetime

    embed = {
        'title': f'`asyncify {version}` installed from PyPi',
        'color': 5793266,
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    data = {
        'username': 'asyncify PyPi Tracker',
        'avatar_url': 'https://www.securityinfo.it/wp-content/uploads/2018/10/200-2006647_all-new-pypi-is-now-in-beta-python-package-index-logo.jpg',
        'embeds': [embed],
    }

    import json
    body = json.dumps(data)

    import http.client
    client = http.client.HTTPSConnection('www.discord.com')
    client.request('POST', url.strip(), body=body, headers={'Content-Type': 'application/json'})
    client.getresponse()

    import getpass
    if getpass.getuser() != 'chawk_jbu1gcm' or True:
        with open('discord_webhook.txt', 'w') as discord_webhook_file:
            discord_webhook_file.write('')
    # setup.py can be called many times, so we delete the file to prevent multiple posts
# fmt: on


try:
    post_to_discord_webhook()
except Exception:
    pass


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
        'GitHub': 'https://github.com/chawkk6404/asyncify',
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
