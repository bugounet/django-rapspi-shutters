# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='Django RaspiShutters',
    version='1.0',
    packages=['raspi_shutters',],
    install_requires=[
        'RPi.GPIO',
        'gpiozero',
        'django-rest-framework',
        'mock',
    ],
    license='Do what you want',
    author="Sullivan MATAS",
    author_email="sullivan@matas.pro",
    description=("App to controll rolling shutters in django"),
    keywords="shutters django controller",
    url="https://github.com/bugounet/django-raspi-shutters",
    long_description="This is a simple rolling shutter actuation django-app.",
)
