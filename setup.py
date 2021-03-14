from setuptools import setup, find_packages

setup(
    name="sns_email",
    packages=find_packages(),
    entry_points={
        'console_scripts': ['sns-email=sns_email.command_line:main'],
    },
    test_suite="tests",
)
