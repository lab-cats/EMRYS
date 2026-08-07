"""NORAD internal Python package.

Public workflow entry points remain the owner-local scripts under ``stages``,
``analyses``, ``evidence``, ``ingestion``, and ``reporting``.  This package
exists so those entry points can share narrow implementation modules without
copying shared import machinery.
"""

