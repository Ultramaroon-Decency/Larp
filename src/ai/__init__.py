# ai package

# This file makes src/ai a package. Keep package-level exports minimal here.
from .data_fetcher import DataFetcher

__all__ = ["DataFetcher"]
