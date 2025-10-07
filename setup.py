import setuptools
from pathlib import Path

README = (Path(__file__).parent/"README.md").read_text(encoding="utf8")

setuptools.setup(
    name="streamlit-paypal",
    version="0.1.14",
    author="TEENLU",
    author_email="ivanru372@gmail.com",
    description="PayPal payment integration for Streamlit apps",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/streamlit-paypal",  # TODO: Update with actual repo
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
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