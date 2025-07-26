from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arizona-forum-api-async",
    version="1.1.3",
    author="fakelag28",
    author_email="fakelag712@gmail.com",
    description="Асинхронная Python библиотека для взаимодействия с форумом Arizona RP (forum.arizona-rp.com) без необходимости получения API ключа.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fakelag28/Arizona-Forum-API-Async",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "aiohttp",
        "aiohttp-socks",
        "beautifulsoup4",
        "dukpy",
        "lxml",
    ],
) 