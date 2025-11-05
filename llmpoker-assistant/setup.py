from setuptools import setup, find_packages

setup(
    name="llmpoker-assistant",
    version="0.1.0",
    description="Real-time poker decision co-pilot with accountability",
    author="PokerGPT Team",
    author_email="",
    url="https://github.com/MrMoshkovitz/PokerGPT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "transformers>=4.30.0",
        "pillow>=9.5.0",
        "mss>=9.0.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "aiosqlite>=0.19.0",
        "openai>=1.0.0",
        "google-generativeai>=0.3.0",
        "treys>=0.1.8",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "llmpoker=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
