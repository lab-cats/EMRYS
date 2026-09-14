# Report styles

[`run_report.css`](run_report.css) is shared by both self-contained HTML views.
It is checked for external resource references before the template embeds it.
View-specific banners, scientific figures, candidate records, and figure guides
use one stylesheet; CSS sets presentation, not evidence policy.

Print rules set page margins, remove sticky positioning, and prevent horizontal
overflow in scientific content. They keep the three relative output links visible,
render the selected-candidate index as ranked cards rather than a wide table,
keep compact evidence blocks and four-pair batches together, retain two-column
record and figure-guide grids, and start major figure/guide sections on new pages.
Selectors change with the template; they are not a public styling API.

[Report tests](../../../../tests/reporting/test_report.py) and installed-wheel
resource/render smoke check the stylesheet and its use.
