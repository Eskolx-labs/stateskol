"""Reference checks. Owner: Yonas.

Week 1 proof that our numbers match the trusted libraries. Yonas fills this
in as owner code lands: same dataset, same result, stated tolerance. This
file runs in CI, so keep it fast and deterministic.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Yonas wires reference checks as week 1 code lands")
