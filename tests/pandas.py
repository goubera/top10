class Series:
    def __init__(self, data=None):
        self.data = list(data) if data is not None else []

    def fillna(self, value):
        return Series([value if x is None else x for x in self.data])

    def __ge__(self, other):
        return Series([x >= other for x in self.data])

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


class DataFrame:
    def __init__(self, data=None, columns=None):
        if data is None:
            self.columns = list(columns) if columns is not None else []
            self._rows = []
        elif isinstance(data, dict):
            self.columns = list(columns) if columns is not None else list(data.keys())
            length = len(next(iter(data.values()))) if data else 0
            self._rows = []
            for i in range(length):
                row = {}
                for col in self.columns:
                    col_data = data.get(col, [None] * length)
                    row[col] = col_data[i]
                self._rows.append(row)
        elif isinstance(data, list):
            self._rows = [dict(r) for r in data]
            if columns is not None:
                self.columns = list(columns)
            elif data:
                self.columns = list(data[0].keys())
            else:
                self.columns = []
        else:
            raise TypeError("Unsupported data type for DataFrame")

    @property
    def empty(self):
        return len(self._rows) == 0

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, key):
        if isinstance(key, str):
            return Series([row.get(key) for row in self._rows])
        if isinstance(key, Series):
            bools = list(key)
            filtered = [row for row, flag in zip(self._rows, bools) if flag]
            return DataFrame(filtered, columns=self.columns)
        raise KeyError(f"Unsupported key type: {type(key)!r}")

    def head(self, n):
        return DataFrame(self._rows[:n], columns=self.columns)

    def sort_values(self, by, ascending=True):
        if isinstance(by, str):
            by = [by]
        if isinstance(ascending, bool):
            ascending = [ascending] * len(by)

        def sort_key(row):
            values = []
            for col, asc in zip(by, ascending):
                val = row.get(col)
                values.append(val if asc else (-val if isinstance(val, (int, float)) else val))
            return tuple(values)

        sorted_rows = sorted(self._rows, key=sort_key)
        return DataFrame(sorted_rows, columns=self.columns)


__all__ = ["DataFrame", "Series"]
