from collections.abc import MutableMapping
from typing import Iterator, Dict, TypeVar, Tuple, Hashable, Any
import pandas as pd
import re


_T = TypeVar("_T")
_KT = TypeVar("_KT")  # Key type.
_VT = TypeVar("_VT")  # Value type.
_T_co = TypeVar("_T_co", covariant=True)  # Any type covariant containers.
_V_co = TypeVar("_V_co", covariant=True)  # Any type covariant containers.
_KT_co = TypeVar("_KT_co", covariant=True)  # Key type covariant containers.
_VT_co = TypeVar("_VT_co", covariant=True)  # Value type covariant container

pattern = re.compile(r"\((.+)\)")

class Params(MutableMapping):

    def __init__(self, data: Dict[Hashable, Any], r: pd.Series, **kwargs) -> None:
        super().__init__()
        self._store = dict()
        self._r = r
        if data is None:
            data = {}
        '''
        if a dict was passed, call free function update() to add to the internal store.  
        This function will call __set_item()__. So the internal store must be ready before update() called 
        '''
        self.update(dict(data, **kwargs))

    def _transform_value(self, v: _VT) -> Tuple[_VT, _VT]:
        '''
        This method is to transform the variable to the actual value. according to the data passed
        "title"  -> "title"  (no change)
        "$title" -> "Python Data Science"

        :param v:  Constant or a variable with $ prefixed. ex. title or $title
        :return: (original value, transformed value). For the constant, the two values should be same
        '''
        nv = v
        if type(v) == str and v.startswith("$"):
            s = v.split("$")[1]
            nv = self._r[s]
        return (v, nv)

    def __setitem__(self, k: _KT, v: _VT) -> None:
        self._store[k] = self._transform_value(v)

    def __delitem__(self, k: _KT) -> None:
        del self._store[k]

    def __getitem__(self, k: _KT) -> _VT_co:
        return self._store[k]

    def __len__(self) -> int:
        return len(self._store)

    def __iter__(self) -> Iterator[_T_co]:
        return iter(self._store)

    def get_transformeddict(self) -> Dict[_VT, _VT]:
        return {k: x for k, v in self._store.items() for x in v[1:2]}



class CaseInsensitiveDict(MutableMapping):
    def __init__(self, data: Dict, **kwargs) -> None:
        super().__init__()
        self._store = dict()
        if data is None:
            data = {}
        self.update(dict(data, **kwargs))

    def __setitem__(self, k: _KT, v: _VT) -> None:
        self._store[k.lower()] = (k, v)

    def __delitem__(self, k: _KT) -> None:
        del self._store[k.lower()]

    def __getitem__(self, k: _KT) -> _VT_co:
        return self._store[k.lower()][1]

    def __len__(self) -> int:
        return len(self._store)

    def __iter__(self) -> Iterator[_T_co]:
        return (k for k, v in self._store.values())

class Book(dict):
    def __init__(self, data:Dict[Hashable, Any], tag: _T) -> None:
        super().__init__()
        self.tag = tag
        if data is not None:
            self.update(data)

    def get_info (self, key) -> str:
        '''
        To get the content based on the selector and content type
        string or text  -->  tag.select_one(selector).string or .text
        attribite(att_name)  -->  tag.select_one(selector)[att_name]

        :param key:  key or book information including, booklist, price, desc, blink etc
        :return: the content
        '''
        d = self.get(key)
        selector = d["selector"]
        content_type= d["content_type"]

        t = self.tag.select_one(selector)
        if content_type == "string":
            return str.strip(t.string)
        elif content_type == "text":
            return str.strip(t.text)
        elif content_type.startswith("attribute"):
            z = re.search(pattern, content_type)
            return t[z.groups()[0]]


if __name__ == "__main__":

    p = {'ac': '1', 'ac.morein': 'true', 'ac.title': '$title', 'query': '$title'}
    r = pd.DataFrame({"title": ["mybook"]})
    params = Params(p, r.loc[0])
    d = {k:x for k, v in params.items() for x in v[1:2]}

    print(d)



