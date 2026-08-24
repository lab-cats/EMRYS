"""Bounded local-pilot orchestration package.

The public owner APIs live in the canonical ``all_pass`` and ``normalization``
modules. Neutral reporting projection lives under
``emrys.contracts.orchestration.projection``. Keeping this package marker free
of eager imports lets narrow commands such as semantic validation run without
loading unrelated workflow dependencies.
"""
