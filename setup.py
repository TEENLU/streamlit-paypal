import setuptools
from pathlib import Path

README = (Path(__file__).parent/"README.md").read_text(encoding="utf8")

setuptools.setup(
    name="streamlit-paypal",
    version="1.0.0",
    author="TEENLU",
    author_email="ivanru372@gmail.com",
    description="PayPal payment integration for Streamlit apps",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/TEENLU/streamlit-paypal",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    license_files=("LICENSE",),
    install_requires=[
        # By definition, a Custom Component depends on Streamlit.
        # If your component has other Python dependencies, list
        # them here.
        "streamlit>=1.28.1",
        "requests>=2.31.0",     # For PayPal API integration
        "python-dotenv==1.0.1"
    ],
)