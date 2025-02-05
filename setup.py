from setuptools import setup

setup(

    name='wave',  
    version='0.2',
    py_modules=['main'],  
    install_requires=[
        'requests',
        'questionary'
    ],
    entry_points={
        'console_scripts': [
            'wave = main:main',  
        ],
    },
)
