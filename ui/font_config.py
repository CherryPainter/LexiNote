"""字体配置数据类。

把原先散落在各 UI 页面、形如 ``{'header': (...), 'normal': (...)}`` 的裸字典
统一收敛为 ``FontConfig`` 数据类：

- 全部已知字体键都带默认值，从根源上杜绝 ``KeyError``；
- 实现 ``__getitem__`` / ``get`` / ``__contains__``，使其可像字典一样使用，
  因此上百处 ``self.font_config['xxx']`` 访问点无需改动即可获得兜底；
- 提供 ``merge(overrides)`` 类方法，用传入的字典 / 另一个 ``FontConfig``
  覆盖默认值，缺失键自动补默认值。
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict, Mapping, Optional, Tuple

# 字体元组，例如 ("SimHei", 12) 或 ("SimHei", 16, "bold")
FontTuple = Tuple[Any, ...]


@dataclass
class FontConfig:
    """字体配置（带默认值的不可变数据类）。"""

    title: FontTuple = ("SimHei", 24, "bold")
    header: FontTuple = ("SimHei", 18, "bold")
    normal: FontTuple = ("SimHei", 12)
    small: FontTuple = ("SimHei", 10)
    button: FontTuple = ("SimHei", 12)

    # 兼容历史 / 测试传入的非标准键
    _extra: Dict[str, FontTuple] = field(default_factory=dict, repr=False, compare=False)
    # 访问未知键时的兜底字体，绝不抛 KeyError
    _fallback: FontTuple = field(default=("SimHei", 12), init=False, repr=False, compare=False)

    # ---- 字典式访问（保持既有 self.font_config['x'] 用法不变）----

    def _known_keys(self) -> set:
        return {f.name for f in fields(self) if f.name not in ("_extra", "_fallback")}

    def __getitem__(self, key: str) -> FontTuple:
        if key in self._known_keys():
            return getattr(self, key)
        if key in self._extra:
            return self._extra[key]
        return self._fallback

    def get(self, key: str, default: Any = None) -> Any:
        if key in self:
            return self[key]
        return default

    def __contains__(self, key: str) -> bool:
        return key in self._known_keys() or key in self._extra

    def keys(self):
        return list(self._known_keys()) + list(self._extra.keys())

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    # ---- 构造辅助 ----

    @classmethod
    def merge(cls, overrides: Optional[Any] = None) -> "FontConfig":
        """用 overrides 覆盖默认值，缺失键补默认值。

        overrides 可以是 dict、``FontConfig`` 实例或 ``None``。
        """
        known = {f.name for f in fields(cls) if f.name not in ("_extra", "_fallback")}
        data: Dict[str, Any] = {}
        if overrides is not None:
            if isinstance(overrides, FontConfig):
                for k in known:
                    data[k] = getattr(overrides, k)
                data.update(dict(overrides._extra))
            elif isinstance(overrides, Mapping):
                data.update(dict(overrides))
        kwargs = {k: v for k, v in data.items() if k in known}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(_extra=extra, **kwargs)
