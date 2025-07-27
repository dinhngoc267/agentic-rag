# Python

class EntityManager:
    """
    Assigns and retrieves unique IDs for mentions.
    Can upgrade logic later without touching entity code.
    """
    def __init__(self, id_format="mention_{:03d}"):
        self._map = {}
        self._counter = 0
        self._id_format = id_format

    def get_id(self, mention_str: str) -> str:
        key = mention_str.lower()
        if key not in self._map:
            self._counter += 1
            self._map[key] = self._id_format.format(self._counter)
        return self._map[key]

    def reset(self):
        """Resets the mapping and counter (useful for new documents or tests)."""
        self._map.clear()
        self._counter = 0

    def as_dict(self):
        """Returns a copy of the mapping."""
        return dict(self._map)

