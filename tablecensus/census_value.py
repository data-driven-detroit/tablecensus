from dataclasses import dataclass
import numbers
import numpy as np




@dataclass(frozen=True, slots=True)
class CensusValue:
    estimate: float | int | None
    error: float | int | None
    table: str | None = None

    def _handle_table(self, other) -> str | None:
        """Determine the table value when combining two CensusValues."""
        if self.table == other.table:
            return self.table
        return None

    def _check_estimates(self, other) -> bool:
        """Check if both estimates are not None."""
        return self.estimate is not None and other.estimate is not None

    def _check_errors(self, *values) -> bool:
        """Check if all error values are not None."""
        return all(v.error is not None for v in values if isinstance(v, CensusValue))

    def __add__(self, other):
        if not self._check_estimates(other):
            return CensusValue(None, None)

        table = self._handle_table(other)
        estimate = self.estimate + other.estimate

        if not self._check_errors(self, other):
            return CensusValue(estimate, None, table)

        return CensusValue(
            estimate,
            np.sqrt(self.error**2 + other.error**2),
            table
        )
    
    # Addition is commutative
    __radd__ = __add__
    
    def __sub__(self, other):
        if not self._check_estimates(other):
            return CensusValue(None, None)

        table = self._handle_table(other)
        estimate = self.estimate - other.estimate

        if not self._check_errors(self, other):
            return CensusValue(estimate, None, table)

        return CensusValue(
            estimate,
            np.sqrt(self.error**2 + other.error**2),
            table
        )

    def __rsub__(self, other):
        if not self._check_estimates(other):
            return CensusValue(None, None)

        table = self._handle_table(other)
        estimate = other.estimate - self.estimate

        if not self._check_errors(self, other):
            return CensusValue(estimate, None, table)

        return CensusValue(
            estimate,
            np.sqrt(self.error**2 + other.error**2),
            table
        )
    
    def __mul__(self, other: int | float):
        if not isinstance(other, numbers.Number):
            raise TypeError(
                f"CensusValues cannot be multiplied with {type(other).__name__}, only number values."
            )

        if self.estimate is None:
            return CensusValue(None, None)

        estimate = self.estimate * other

        if self.error is None:
            return CensusValue(estimate, None, self.table)

        return CensusValue(
            estimate,
            self.error * other,
            self.table
        )

    # Multiplication is commutative
    __rmul__ = __mul__

    def __truediv__(self, other):
        try:
            if isinstance(other, CensusValue):
                if not self._check_estimates(other):
                    return CensusValue(None, None)

                estimate = self.estimate / other.estimate
                table = self._handle_table(other)

                if not self._check_errors(self, other):
                    return CensusValue(estimate, None, table)

                # If the estimates come from the same universe, the errors will be
                # correlated. The
                vsu = self.error**2 - (estimate * other.error)**2
                vdu = self.error**2 + (estimate * other.error)**2

                if (self.table is not None) and (self.table == other.table) and (vsu > 0):
                    v = vsu
                else:
                    v = vdu

                error = (1 / other.estimate) * np.sqrt(v)

                return CensusValue(estimate, error, table)

            if isinstance(other, numbers.Number):
                if self.estimate is None:
                    return CensusValue(None, None)

                estimate = self.estimate / other

                if self.error is None:
                    return CensusValue(estimate, None, self.table)

                return CensusValue(
                    estimate,
                    self.error / other,
                    self.table
                )
        except ZeroDivisionError:
            return CensusValue(None, None)

    def __rtruediv__(self, other):
        if isinstance(other, CensusValue):
            try:
                if not self._check_estimates(other):
                    return CensusValue(None, None)

                estimate = other.estimate / self.estimate
                table = self._handle_table(other)

                if not self._check_errors(self, other):
                    return CensusValue(estimate, None, table)

                # If the estimates come from the same universe, the errors will be
                # correlated. The
                vsu = other.error**2 - (estimate * self.error)**2
                vdu = other.error**2 + (estimate * self.error)**2

                if (self.table is not None) and (self.table == other.table) and (vsu > 0):
                    v = vsu
                else:
                    v = vdu

                error = (1 / self.estimate) * np.sqrt(v)

                return CensusValue(estimate, error, table)
            except ZeroDivisionError:
                return CensusValue(None, None)

        if isinstance(other, numbers.Number):
            if self.estimate is None:
                return CensusValue(None, None)

            estimate = other / self.estimate

            if self.error is None:
                return CensusValue(estimate, None, self.table)

            return CensusValue(
                estimate,
                other / self.error,
                self.table
            )
    
    def __repr__(self):
        return f"CensusValue({self.estimate})"
