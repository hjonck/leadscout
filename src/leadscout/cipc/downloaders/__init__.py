"""CIPC CSV downloaders package.

This package provides functionality for downloading and processing CIPC 
(Companies and Intellectual Property Commission) CSV data files according
to the research-validated approach.
"""

from .csv_downloader import CIPCCSVDownloader

__all__ = ["CIPCCSVDownloader"]