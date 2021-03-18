from setuptools import setup, find_packages

setup(
    name="sns_email",
    version="0.3.2",
    author="https://github.com/fogninid",
    url="https://github.com/fogninid/sns-email",
    python_requires=">=3.8",
    packages=find_packages(),
    entry_points={
        'console_scripts': ['sns-email=sns_email.command_line:main'],
    },
    test_suite="tests",
)
