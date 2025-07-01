from setuptools import setup, find_packages
import pathlib

# Use pathlib for robust path handling
here = pathlib.Path(__file__).parent.resolve()

with open(here / "requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="morsegramvis",
    version="0.1.0",
    description="Granular visualization and analysis toolkit",
    author="Your Name",
    packages=find_packages(include=["core*", "ui*", "colormap*", "Notebooks*", "morsegramvis*"]),
    install_requires=requirements,
    include_package_data=True,
    package_data={
        '': ['assets/*', 'colormap/*', 'ui/icons/*']
    },
    entry_points={
        'console_scripts': [
            'morsegramvis=morsegramvis.start:main',
        ],
    },
    python_requires='>=3.8',
)
