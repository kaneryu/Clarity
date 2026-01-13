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
            return self.namespacedIdentifier == other and self.type == other.type
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
