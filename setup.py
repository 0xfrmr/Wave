from setuptools import setup

setup(

    name='Wave',  
    version='0.2',
    py_modules=['Wave'],  
    install_requires=[
        'requests',
        'questionary'
    ],
    entry_points={
        'console_scripts': [
            'Wave = Wave:main',  
        ],
    },
)
