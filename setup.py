from setuptools import setup, find_packages

setup(
    name="youtube-toolkit",
    version="1.1.0",
    description="Unified YouTube API Client and Video Analyzer",
    author="MK3000-AKA",
    author_email="",
    url="https://github.com/MK3000-AKA/youtube-analyzer",
    packages=find_packages(),
    py_modules=["youtube_analyzer"],
    install_requires=[],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "youtube-analyzer=youtube_analyzer:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)