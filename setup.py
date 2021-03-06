"""update-conf.py setup.py file
"""

import os
from os.path import abspath, dirname, join, isfile
import shutil
from distutils import log
from setuptools import setup, Command
from setuptools.command.register import register
from setuptools.command.install import install

from update_conf_py import main

# Consts
GITHUB_URL = "https://github.com/rarylson/update-conf.py"
README_MD = "README.md"
README_RST = "README.rst"

# Important vars
cur_dir = abspath(dirname(__file__))
readme_md = join(cur_dir, README_MD)
readme_rst = join(cur_dir, README_RST)
sample_config = join("samples", main.CONFIG_NAME)
sample_config_path = join(cur_dir, sample_config)
# Get description from the first line of the module docstring.
description = main.__doc__.split('\n')[0]
# Get the long description from the 'README.rst' file (if it exists). Else,
# use the module doc string.
# The 'README.rst' is required when registering on Pypi.
long_description = ""
using_rst = False
try:
    with open(readme_rst, 'r') as f:
        long_description = f.read()
        using_rst = True
except IOError:
    long_description = main.__doc__


class GenerateRstCommand(Command):
    """Generate a README.rst file

    This file can be used after in the register command.
    """

    description = "generate a README.rst file from README.md"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        if isfile(readme_rst):
            os.remove(readme_rst)

    def run(self):
        import tempfile
        import shutil
        import re

        import pypandoc

        tmp_readme_md = join(tempfile.gettempdir(), README_MD)
        shutil.copy(readme_md, tmp_readme_md)
        try:
            with open(tmp_readme_md, "r") as f:
                md = f.read()
            # Convert links that points to a relative URL
            # The markdown file may be relative URLs (like [Page](page)).
            # However, we do not want these links in Pypi (they will be
            # broken). We want to replace them by absolutive URLs (like
            # [Page]({url}/blob/master/page)).
            # For now, the conversions are hardcoded.
            md_link_re = r"\(LICENSE\)"
            md_link_new = r"({0}/blob/master/LICENSE)".format(GITHUB_URL)
            new_md = re.sub(md_link_re, md_link_new, md)
            md_link_re = r"\(CHANGELOG\.md\)"
            md_link_new = r"({0}/blob/master/CHANGELOG.md)".format(GITHUB_URL)
            new_md = re.sub(md_link_re, md_link_new, new_md)
            with open(tmp_readme_md, "w") as f:
                f.write(new_md)
            # Now, convert to RST
            rst = pypandoc.convert(tmp_readme_md, "rst")
            with open(readme_rst, "w") as f:
                f.write(rst)
        finally:
            os.remove(tmp_readme_md)


class RegisterCommand(register):
    """Check if we're using README.rst before registering in Pypi
    """

    def finalize_options(self):
        if not using_rst:
            raise Exception("{} file not found".format(README_RST))

        return register.finalize_options(self)


class InstallCommand(install):
    """Install the global config file

    The global config file will be installed only if:
    - The file doesn't exist yet
    - We have write permission in the global system config dir
    """

    def run(self):
        result = install.run(self)
        etc_dir = dirname(main.SYSTEM_CONFIG)
        if not isfile(main.SYSTEM_CONFIG):
            if os.access(etc_dir, os.W_OK):
                log.info("Copying {0} to {1}".format(
                    sample_config, main.SYSTEM_CONFIG))
                shutil.copy(sample_config_path, main.SYSTEM_CONFIG)
            else:
                log.warn(
                    "Skiping copy of {0} to {1}. You do not have write "
                    "permission in the {2} dir.".format(
                        sample_config, main.SYSTEM_CONFIG, etc_dir))
        else:
            log.info(
                "Skipping copy of {0} to {1}. Config file already "
                "exists.".format(sample_config, main.SYSTEM_CONFIG))

        return result


# Setup
setup(
    # Main software info
    name=main.__program__,
    version=main.__version__,
    description=description,
    long_description=long_description,
    license=main.__license__,
    author=main.__author__,
    author_email=main.__email__,
    url=GITHUB_URL,
    # FIXME: Currently, setuptools do not understand this option (it's used
    # only by twine). When using setuptools, for now, ignore the warning. In
    # a future, only pass this option when using twine.
    bugtrack_url="{0}/issues".format(GITHUB_URL),
    download_url="{0}/tarball/{1}".format(GITHUB_URL, main.__version__),
    keywords="system unix config split snippets sysadmin",
    packages=["update_conf_py"],

    # Requirements
    install_requires=[
        "argparse>=1.2",
        "configparser>=2.3",
    ],

    # Classifiers
    # See: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],

    # Entry points
    # The script itself is defined here.
    entry_points={
        "console_scripts": [
            "update-conf.py = update_conf_py:run",
        ],
    },

    # Data files
    data_files=[
        (join("share", main.__program__), [sample_config, ]),
    ],

    # Extra
    extras_require={
        "dev": [
            "setuptools>=0.8",
            "pypandoc>=0.9",
        ],
        "test": [
            "unittest2>=1.0.0",
            "coverage>=3.7",
            "flake8>=2.2",
            "pep8-naming>=0.2",
            "check-manifest>=0.22",
        ],
    },

    # Tests
    test_suite="tests",

    # Commands
    cmdclass={
        "generate_rst": GenerateRstCommand,
        "register": RegisterCommand,
        "install": InstallCommand,
    }
)
