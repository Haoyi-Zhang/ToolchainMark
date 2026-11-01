# Retained owned native activity

The raw rows, object bytes, original source identities and measurements in this
directory are unchanged. The current admission implementation has since been
repaired; the saved activity is not a rerun of that later implementation.

The data-only deriver checks the six exact registered producer identities. Five
still match their working files. The admission input is authenticated against
the matching preserved bytes in `../native-execution/source-snapshot/`; those
bytes are shared with the separately recorded Linux activity and are never
imported or executed by this verification. Missing, corrupt or substituted
preimages remain errors. Changing the source identities in the summary to those
of a later checkout is also rejected.

This validates the retained activity and its source binding. It neither adds
measurements nor demonstrates current-code performance or deployment.
