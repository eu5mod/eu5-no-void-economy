# CBP Adapters

These adapters compile CBP balance policy into CBG specifications. They may
import CBP discovery and edge-case compilers from the repository-level
`tools/` directory.

They do not materialize runtime files themselves. `generate_all.sh` invokes an
adapter to produce JSON, then invokes the generic CBG materializer.

Parity validators live under `tools/cbg/validator/cbp/` because they validate
the host integration rather than the adapter mechanism itself.
