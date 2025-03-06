from setuptools import setup

setup(
    name="wave",
    version="0.3",
    py_modules=["main"],
    install_requires=["requests", "questionary", "beautifulsoup4"],
    entry_points={
        "console_scripts": [
            "wave = main:main",
        ],
    },
)
