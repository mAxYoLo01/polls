from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="interactions-polls",
    version="0.0.1",
    description="interactions.py polls",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mAxYoLo01/polls",
    author="mAxYoLo01",
    author_email="maxyolo01.ytb@gmail.com",
    license="GNU",
    packages=["interactions.ext.polls"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=["discord-py-interactions"],
)
