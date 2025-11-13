from __future__ import absolute_import, division, print_function

__metaclass__ = type

# Custom exceptions for the sap_launchpad collection.


class SapLaunchpadError(Exception):
    # Base exception for all application-specific errors.
    pass


class AuthenticationError(SapLaunchpadError):
    # Raised for errors during the authentication process.
    pass


class AuthorizationError(SapLaunchpadError):
    # Raised when a user is not authorized to perform an action.
    pass


class DownloadError(SapLaunchpadError):
    # Raised for errors during the download process, like a checksum mismatch.
    pass


class FileNotFoundError(SapLaunchpadError):
    # Raised when a searched file cannot be found.
    pass
