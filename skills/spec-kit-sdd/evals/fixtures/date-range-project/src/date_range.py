from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def contains(self, value: date) -> bool:
        # Fixture defect: the documented end boundary should be inclusive.
        return self.start <= value < self.end
