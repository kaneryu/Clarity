from .registry import list_providers, get_provider
from src.providerInterface.globalModels.identifier import NamespacedTypedIdentifier


def get_all_downloads() -> list[NamespacedTypedIdentifier]:
    """Get every provider's downloaded songs, then dump it all into a list of NSIDs"""
    dl_list = []
    for i in list_providers():
        provider_class = get_provider(i)
        if provider_class is None:
            continue
        datastore = provider_class.DATASTORE
        ds_list = datastore.getAll()
        ds_cleaned: list[str] = []
        # Now we filter out the metadata entries. The providers should store ....
        # metadata files beside the actual song files, and we only want the titles of the actual song files
        for key, path in ds_list.items():
            if not path.endswith(".json"):
                ds_cleaned.append(key)

        for i in ds_cleaned:
            dl_list.append(provider_class.convert_to_namespaced_id(i))

    return dl_list
