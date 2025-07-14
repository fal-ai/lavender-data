from typing import Optional

from lavender_data.server.registries.filter import Filter


class MinMaxFilter(Filter):
    name = "min_max"

    def filter(
        self,
        sample: dict,
        *,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> bool:
        try:
            value = float(sample[column])
        except (ValueError, TypeError, KeyError):
            return False

        if min_value is not None and value <= float(min_value):
            return False
        if max_value is not None and value >= float(max_value):
            return False
        return True
