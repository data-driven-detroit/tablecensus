from dataclasses import dataclass
import numbers
import numpy as np



@dataclass(frozen=True, slots=True)
class CensusValue:
    estimate: float | int
    error: float | int
    table: str | None = None

    def __add__(self, other):
        if self.table == other.table:
            table = self.table
        else:
            table = None

        return CensusValue(
            self.estimate + other.estimate,
            np.sqrt(self.error**2 + other.error**2),
            table
        )
    
    # Addition is commutative
    __radd__ = __add__
    
    def __sub__(self, other):
        if self.table == other.table:
            table = self.table
        else:
            table = None

        return CensusValue(
            self.estimate - other.estimate,
            np.sqrt(self.error**2 + other.error**2),
            table
        )

    def __rsub__(self, other):
        if self.table == other.table:
            table = self.table
        else:
            table = None

        return CensusValue(
            other.estimate - self.estimate,
            np.sqrt(self.error**2 + other.error**2),
            table
        )
    
    def __mul__(self, other: int | float):

        # Accepts only scalars
        if not isinstance(other, numbers.Number):
            raise TypeError(
                f"CensusValues cannot be multiplied with {type(other).__name__}, only number values."
            )

        return CensusValue(
            self.estimate * other,
            self.error * other,
            self.table
        )

    def __truediv__(self, other):
        # This should accept either numeric or censusvals
        if isinstance(other, CensusValue):
            estimate = self.estimate / other.estimate
            
            # If the estimates come from the same universe, the errors will be 
            # correlated. The 
            vsu = self.error**2 - (estimate * other.error)**2
            vdu = self.error**2 + (estimate * other.error)**2

            if (self.table is not None) and (self.table == other.table) and (vsu > 0):
                v = vsu
            else:
                v = vdu
            
            if self.table == other.table:
                table = self.table
            else:
                table = None

            error = (1 / other.estimate) * np.sqrt(v)

            return CensusValue(estimate, error, table)

        if isinstance(other, numbers.Number):
            return CensusValue(
                self.estimate / other,
                self.error / other,
                self.table
            )

    def __rtruediv__(self, other):
        if isinstance(other, CensusValue):
            estimate = other.estimate / self.estimate
            
            # If the estimates come from the same universe, the errors will be 
            # correlated. The 
            vsu = other.error**2 - (estimate * self.error)**2
            vdu = other.error**2 + (estimate * self.error)**2

            if (self.table is not None) and (self.table == other.table) and (vsu > 0):
                v = vsu
            else:
                v = vdu
            
            if self.table == other.table:
                table = self.table
            else:
                table = None

            error = (1 / self.estimate) * np.sqrt(v)

            return CensusValue(estimate, error, table)

        if isinstance(other, numbers.Number):
            return CensusValue(
                other / self.estimate,
                other / self.error,
                self.table
            )
    
    def __repr__(self):
        return f"CensusValue({self.estimate})"
