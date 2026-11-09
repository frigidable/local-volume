# Calculated parameters

The API exposes a separate derived list in the galaxy detail response; the
frontend renders it below the catalog parameter table.

The distance modulus (m-M) is source-native for records with
basis="modulus" in the LV SAO importer. The importer already converts
that modulus to distance via D[Mpc] = 10 ** ((mu - 25) / 5), while the
current PR #8 schema stores only dist. Therefore the original modulus
and provenance require a separate modeling correction before full ingestion.
Neither mu nor dist is reintroduced in the calculated-parameters panel.

For calculations such as Ks luminosity that require mu, the domain API
accepts a source modulus explicitly. Until the source modulus is stored,
the numerical inverse of an adopted distance may be used only as an
internal algebraic conversion; it is not an independent measurement or
a new derived catalog parameter. Rows whose basis is "distance_only"
retain the directly supplied distance without inventing a measured mu.

The other formulas are wired but their inputs are deliberately not guessed.
The current summary schema does not expose a validated numerical morphology
T, a model-compatible b/a, HI W50, B-band Galactic extinction, or a verified
Ks magnitude. type_name is not T, b50/a50 is not automatically a valid model
axis ratio, and kt is not automatically interchangeable with Ks. Missing
W50 is not treated as zero internal attenuation.

Tidal calculations require an explicitly certified, versioned complete
neighbor sample. The API currently has no such input and returns null with a
reason, rather than provisional theta values.

No production database is changed. Once source values and a frozen neighbor
snapshot are available, connect them to the domain function by keyword.
The integration branch is stacked on PR #8, and carries unchanged modules
and tests from PRs #5–#7 until those dependencies are merged.
