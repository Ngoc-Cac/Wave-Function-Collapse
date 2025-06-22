import heapq as hq

from typing import (
    Any,
    Generic,
    Iterable,
    Iterator,
    Optional,
    TypeVar,
)
T = TypeVar('T')


# item = [item, count, is_removed]
# count used for FIFO structuring when priority is equal

def _counter() -> Iterator[int]:
    """
    Generator for infinite counting. Value starts from 1.
    """
    num = 0
    while (num := num + 1): yield num

class PriorityQueue(Generic[T]):
    """
    Priority Queue implemented with minimum heap. This priority queue supports
    updating elements as well as supporting FIFO order for items with equal priority.
    
    ### Usage Notes:
    In order for the queue to work, items in queue need to be:
    - Sortable: must implement a `__lt__` method.
    - Hashable: must implement a `__hash__` method.
    Note that equivalent items (`a == b`) MUST have the same hash (`hash(a) == hash(b)`).
    If not, this might cause unexpected behaviour.
    """
    __slots__ = "_min_heap", "_items_list", "_counter"
    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._min_heap: list[list[T, int, bool]] = []
        self._items_list: dict[T, list[T, int, bool]] = {}
        self._counter = _counter()

        if items:
            for item in items: self.push(item)

    def push(self, item: T) -> None:
        """
        Insert a new item. If item already exists, update the item's priority instead.

        :param T item: Item to push to queue.
        :raise TypeError: If item is not sortable (do not have a `__lt__` method) or
            item is not hashable (do not have a `__hash__` method).
        """
        # Remove item if already exists
        if item in self._items_list:
            # Flag item as removed
            self._items_list[item][2] = True

        new_item = [item, next(self._counter), False]
        self._items_list[item] = new_item
        hq.heappush(self._min_heap, new_item)

    def pop(self) -> T:
        """
        Remove and return the item with smallest priority.

        :return T: The item duh.
        :raise IndexError: If queue is empty.
        """
        while self._min_heap:
            item, _, is_removed = hq.heappop(self._min_heap)
            if not is_removed:
                del self._items_list[item]
                return item
        raise IndexError("Queue is empty")


    def seek(self) -> T:
        """
        Return the item with smallest priority without removal.

        :return T: The item duh.
        """
        while self._min_heap:
            item, _, is_removed = self._min_heap[0]
            if not is_removed: return item
            else: hq.heappop(self._min_heap)

    def clear(self) -> None:
        """
        Clear the queue.
        """
        self._min_heap.clear()
        self._items_list.clear()
        self._counter = _counter()

    def get_attr(self,
        item: T,
        attr: str, *,
        default_value: Any = None
    ) -> Any:
        """
        Get the attribute of item stored in `PriorityQueue`. If item is not found, return
        the default value instead.
        
        :param T item: Item to get attribute of.
        :param str attr: The attribute to get
        :param Any | None default_value: The default value to return if item is not found.
            Value is `None` by default.
        :return Any | None: The value of the attribute. In case the item does not exist, `None`
            is returned.
        :raise AttributeError: If attr does not exist.
        """
        return (
            getattr(self._items_list[item][0], attr)
            if item in self._items_list else default_value
        )


    def __len__(self) -> int: return len(self._items_list)

    def __bool__(self) -> bool: return bool(self._items_list)