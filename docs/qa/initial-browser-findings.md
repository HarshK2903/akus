# Initial browser run — 2026-11-16

12 tests: 10 passed, 2 failed. Both mobile failures (390px and 320px) were axe `scrollable-region-focusable`: the horizontally scrollable academic-year table lacked keyboard focus. Added `tabIndex=0`, a named region and visible focus styling. Layout itself had no viewport overflow. Initial sign-in, navigation, reload, role routing, service failure and the three larger viewport tests passed. Subsequent results are recorded in TEST_RESULTS.md; this finding is retained as observed evidence.
