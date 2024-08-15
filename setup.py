from setuptools import setup, find_packages

setup(
    name="rival_microservice_connector",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sentry-sdk>=2.13.0",
        "pika>=1.3.2"
    ],
    python_requires='>=3.6',
    setup_requires=[
        "setuptools>=61.0",
    ]
)
