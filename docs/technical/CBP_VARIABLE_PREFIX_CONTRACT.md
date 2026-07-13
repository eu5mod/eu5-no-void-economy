# CBP variable-prefix contract

## Prefixes

```txt
cbp_       runtime/internal variable
test_cbp_  test-only variable
gui_cbp_   current or planned GUI variable
```

Classification precedence is:

```txt
GUI > test > runtime
```

A variable used by both a GUI and a test is therefore a `gui_cbp_` variable.

## Planned GUI fields

A variable receives `gui_cbp_` when it is intentionally reserved for a future
GUI even if that GUI is not implemented yet.

The initial planned-GUI registry includes US-17 and US-20 route-accounting
fields such as:

```txt
route quantity
import and selling efficiency
merchant-maintenance efficiency
base and adjusted merchant maintenance
old price-side bonus
route reconciliation delta
sent, received, and lost goods amounts
```

## Scope

The contract applies to CBP-owned:

```txt
scalar variables
temporary scope values
global variables
variable maps
variable lists
```

It does not rename:

```txt
scripted effects
scripted triggers
script-value objects
saved scope aliases
engine identifiers
vanilla variables
Community Mod Framework variables and maps
generator placeholders
localization keys
file names
```

## Validation

```sh
python3 tools/cbp_variable_prefixes.py --check
```

The validator derives classification from executable EU5 sources and fails when:

```txt
a CBP-owned variable retains cbp_ or cbp_
an owned variable has no CBP prefix
a prefix disagrees with GUI/test/runtime classification
a variable conflicts with a saved scope alias
two legacy variables map to the same target name
an unknown external variable needs an explicit ownership decision
```

## Save compatibility

Renaming persistent variables, maps, or lists changes the save schema. Unless a
compatibility bridge is implemented, campaigns written with legacy variable
names are not automatically migrated to the new CBP identifiers.
