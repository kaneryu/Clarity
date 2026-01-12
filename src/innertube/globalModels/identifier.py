"""
Stores dataclasses for Identifier formats used across Innertube.
"""

from dataclasses import dataclass


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
