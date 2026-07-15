# CBG Adapters

Adapters translate host-mod business policy and engine-specific discovery into
resolved CBG JSON specifications. They are not part of the generic
transformation core and may depend on their host repository.

Each host owns a namespaced directory. The current repository provides the CBP
integration under `cbp/`.

The adapter API is not yet standardized. Existing adapters are working
examples and migration surfaces, not a stable external SDK.
