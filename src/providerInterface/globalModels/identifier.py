"""
Stores dataclasses for Identifier formats used across Innertube.
"""

from dataclasses import dataclass
from typing import Union

allIdTypes = Union[
    "NamespacedTypedIdentifier", "NamespacedIdentifier", "SimpleIdentifier"
]


@dataclass(frozen=True, eq=True)
class NamespacedTypedIdentifier:
    """
    Represents an identifier with an associated namespace and data type.
    """

    namespacedIdentifier: "NamespacedIdentifier"
    type: str

    def __str__(self):
        return f"{self.namespacedIdentifier.namespace}:{self.type}:{self.namespacedIdentifier.id}"

    def __repr__(self):
        return f"NamespacedTypedIdentifier(namespacedIdentifier={repr(self.namespacedIdentifier)}, type={self.type})"

    @staticmethod
    def from_string(s: str) -> "NamespacedTypedIdentifier":
        """
        Create a NamespacedTypedIdentifier from a string in the format namespace:type:id
        """
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid format for NamespacedTypedIdentifier: {s}")
        namespace, type_, id_ = parts
        return NamespacedTypedIdentifier(
            namespacedIdentifier=NamespacedIdentifier(
                namespace=namespace,
                id=SimpleIdentifier(id=id_),
            ),
            type=type_,
        )

    @staticmethod
    def from_parts(namespace: str, type_: str, id_: str) -> "NamespacedTypedIdentifier":
        """
        Create a NamespacedTypedIdentifier from its individual parts.
        """
        return NamespacedTypedIdentifier(
            namespacedIdentifier=NamespacedIdentifier(
                namespace=namespace,
                id=SimpleIdentifier(id=id_),
            ),
            type=type_,
        )

    def __eq__(self, other):
        # even if the other is just a NamespacedIdentifier, compare only that part
        if isinstance(other, str):
            try:
                other = NamespacedTypedIdentifier.from_string(other)
                try:
                    other = NamespacedIdentifier.from_string(other)
                    try:
                        other = SimpleIdentifier(id=str(other))
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                return False

        if isinstance(other, NamespacedTypedIdentifier):
            return (
                self.namespacedIdentifier == other.namespacedIdentifier
                and self.type == other.type
            )
        elif isinstance(other, NamespacedIdentifier):
            return self.namespacedIdentifier == other
        elif isinstance(other, SimpleIdentifier):
            return self.namespacedIdentifier.id == other
        return False


@dataclass(frozen=True, eq=True)
class NamespacedIdentifier:
    """
    Represents an identifier with an associated namespace.
    """

    namespace: str
    id: "SimpleIdentifier"

    def __str__(self):
        return f"{self.namespace}:{self.id}"

    def __repr__(self):
        return f"NamespacedIdentifier(namespace={self.namespace}, id={self.id})"

    @staticmethod
    def from_string(s: str) -> "NamespacedIdentifier":
        """
        Create a NamespacedIdentifier from a string in the format namespace:id
        """
        parts = s.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid format for NamespacedIdentifier: {s}")
        namespace, id_ = parts
        return NamespacedIdentifier(
            namespace=namespace,
            id=SimpleIdentifier(id=id_),
        )

    @staticmethod
    def from_parts(namespace: str, id_: str) -> "NamespacedIdentifier":
        """
        Create a NamespacedIdentifier from its individual parts.
        """
        return NamespacedIdentifier(
            namespace=namespace,
            id=SimpleIdentifier(id=id_),
        )

    def __eq__(self, other):
        # even if the other is just a SimpleIdentifier, compare only that part
        if isinstance(other, str):
            try:
                other = NamespacedTypedIdentifier.from_string(other)
            except Exception:
                try:
                    other = NamespacedIdentifier.from_string(other)
                except Exception:
                    try:
                        other = SimpleIdentifier(id=str(other))
                    except Exception:
                        return False

        if isinstance(other, NamespacedTypedIdentifier):
            return self == other.namespacedIdentifier
        elif isinstance(other, NamespacedIdentifier):
            return self.namespace == other.namespace and self.id == other.id
        elif isinstance(other, SimpleIdentifier):
            return self.id == other
        return False


@dataclass(frozen=True, eq=True)
class SimpleIdentifier:
    """
    Represents a simple identifier without namespace.
    """

    id: str

    def __str__(self):
        return self.id

    def __repr__(self):
        return f"SimpleIdentifier({self.id})"

    @staticmethod
    def from_string(s: str) -> "SimpleIdentifier":
        """
        Create a SimpleIdentifier from a string.
        """
        return SimpleIdentifier(id=s)

    @staticmethod
    def from_parts(id_: str) -> "SimpleIdentifier":
        """
        Create a SimpleIdentifier from its individual part.
        """
        return SimpleIdentifier(id=id_)

    def __eq__(self, other):
        if isinstance(other, str):
            try:
                other = NamespacedTypedIdentifier.from_string(other)
            except Exception:
                try:
                    other = NamespacedIdentifier.from_string(other)
                except Exception:
                    try:
                        other = SimpleIdentifier(id=str(other))
                    except Exception:
                        return False

        if isinstance(other, NamespacedTypedIdentifier):
            return self == other.namespacedIdentifier.id
        elif isinstance(other, NamespacedIdentifier):
            return self == other.id
        elif isinstance(other, SimpleIdentifier):
            return self.id == other.id
        return False


def str_to_identifer(
    id_str: str,
) -> Union["NamespacedTypedIdentifier", "NamespacedIdentifier", "SimpleIdentifier"]:
    try:
        return NamespacedTypedIdentifier.from_string(id_str)
    except ValueError:
        try:
            return NamespacedIdentifier.from_string(id_str)
        except ValueError:
            return SimpleIdentifier(id=id_str)
