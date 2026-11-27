# Dataset Cleaning and Handling Pipeline Rules

**Scope note:** This is a framework to instantiate, not a ready-to-run rulebook. Thresholds, severity definitions, allowed formats, and regulatory scope must be set by your organization and recorded in the data contract.

---

# 1. Pipeline Objective

The pipeline must ensure that the dataset is:

- Accurate
- Complete enough for its intended use
- Consistent across fields and sources
- Traceable
- Reproducible
- Safe for downstream analysis, reporting, or modeling
- Compliant with privacy and governance requirements

The pipeline must not silently alter data without recording the change.

---

# 2. Dataset Intake Rules

## 2.1 Source Registration

For every dataset, record:

- Dataset name
- Source system
- Owner or steward
- Ingestion date and time
- Ingestion method
- Expected refresh frequency
- Business meaning
- Expected primary key
- Expected grain
- Approved use cases
- Data classification level
- Applicable regulatory regimes (for example GDPR, CCPA, HIPAA, PCI DSS)

## 2.2 Raw Data Preservation

Rules:

- Preserve the original raw dataset in a write-protected raw zone. Raw data is not modified by cleaning.
- Do not overwrite raw data during cleaning.
- All cleaned versions must be derived from the raw version.
- Every cleaned output must reference the raw version identifier.
- "Immutable" means content is not edited in place. It does not override legal erasure obligations. The raw zone, quarantine zone, rejection zone, and audit layer must all support the controlled erasure process defined in Section 18.4.
- Where raw data contains personal data, apply retention limits and access controls to the raw zone as well.

## 2.3 Schema Discovery

At intake, identify:

- Column names
- Data types
- Field lengths
- Nullable fields
- Primary key candidates
- Foreign key candidates
- Date and time fields
- Categorical fields
- Numeric fields
- Text fields
- Identifier fields
- Sensitive fields

## 2.4 Expected Contract

Each dataset must have a data contract defining:

- Required columns
- Optional columns
- Allowed data types
- Allowed value ranges
- Allowed categorical values
- Uniqueness rules
- Mandatory fields
- Relationship rules
- Freshness expectations
- Approved sentinel and placeholder values and their meaning (see 8.6)
- Expected character encoding

## 2.5 Intake Integrity Verification

Rules:

- Record a checksum or hash of each received file or batch.
- Compare against the source-provided checksum where one exists.
- Reconcile control totals supplied by the source (row counts, sums of key numeric fields) against what was received.
- Detect truncated, partial, or duplicated deliveries before any processing begins.
- A failed integrity check is a dataset-level critical failure (see 21.2).

---

# 3. Structural Validation Rules

## 3.1 Column Presence

Rules:

- Validate that all required columns exist.
- Detect unexpected columns.
- Detect missing columns.
- Detect duplicated column names.
- Detect ambiguous column names.

## 3.2 Column Naming

Rules:

- Standardize column names to a consistent convention.
- Remove leading and trailing spaces.
- Replace unsupported characters.
- Resolve duplicate names caused by source joins.
- Maintain a mapping from original column names to standardized names.

## 3.3 Data Type Validation

Rules:

- Validate that each column matches the expected type.
- Identify numeric fields stored as text.
- Identify date fields stored as text.
- Identify Boolean fields stored as strings or integers.
- Identify mixed-type columns.
- Identify identifier fields that were read as numbers, which drops leading zeros (for example postal codes, account numbers, product codes). Read identifiers as text.
- Identify spreadsheet auto-conversions, such as identifiers turned into scientific notation, gene names or codes turned into dates, and long numbers truncated to 15 digits.
- Store monetary and other exact-precision values as fixed-precision decimals or integer minor units, never as binary floating point.

## 3.4 Row Structure

Rules:

- Detect malformed rows.
- Detect rows with too many or too few fields.
- Detect completely empty rows.
- Detect rows where all values are missing.
- Quarantine structurally invalid rows instead of dropping them silently.

## 3.5 Character Encoding

Rules:

- Declare the expected encoding in the data contract. Prefer UTF-8.
- Detect encoding mismatches and mojibake (for example garbled accented characters).
- Detect byte-order marks, invalid byte sequences, and replacement characters.
- Normalize Unicode representation (for example NFC) for fields used in matching or comparison, and keep the original value where normalization changes it.
- Do not guess the encoding silently. Log any re-encoding performed.

---

# 4. Data Quality Assessment Rules

## 4.0 Profiling Safety

Profiling output (most and least frequent values, minimum and maximum, samples) can expose personal data. Therefore:

- Run sensitive-field identification (Section 18.1) before profiling.
- Mask, suppress, or aggregate profiling statistics for sensitive fields.
- Apply the same access controls to profiling reports as to the data they describe.

Before cleaning, generate a quality profile for each column.

## 4.1 Column-Level Profiling

For each column, calculate:

- Count
- Distinct count
- Missing count
- Missing percentage
- Invalid count
- Invalid percentage
- Minimum value
- Maximum value
- Mean, if numeric
- Median, if numeric
- Standard deviation, if numeric
- Most frequent values
- Least frequent values
- Format violations
- Duplicate values
- Whitespace issues
- Case inconsistency
- Sentinel or placeholder value counts

## 4.2 Dataset-Level Profiling

For the full dataset, calculate:

- Total row count
- Total column count
- Duplicate row count
- Primary key uniqueness
- Cross-field rule violations
- Time range coverage
- Source coverage
- Missingness by row
- Missingness by column
- Outlier counts
- Orphaned records

## 4.3 Post-Cleaning Profiling

Rules:

- Repeat the profile on the cleaned output.
- Compare before and after profiles to confirm that fixes worked and that no unintended changes occurred.
- Include the comparison in the quality report.

---

# 5. Duplicate Handling Rules

## 5.1 Exact Duplicates

Rules:

- Identify records that are identical across all columns.
- Keep one instance unless business rules require retention history.
- Log the number of removed or flagged exact duplicates.

## 5.2 Business-Key Duplicates

Rules:

- Identify duplicates based on the business primary key.
- If duplicates exist, determine whether they are:
  - Invalid duplicates
  - Historical versions
  - Slowly changing records
  - Repeated events
- Do not remove business-key duplicates automatically unless the rule is explicit.

## 5.3 Duplicate Resolution

When duplicates are found:

1. Preserve all original records in the audit layer.
2. Apply a deterministic survivorship rule, evaluated in the order below. The order must be fixed in the rule definition and versioned.
   1. **Trusted source** ranking, using the documented source hierarchy.
   2. **Most recent valid record**, where timestamps are reliable. Validity is checked before recency.
   3. **Most complete record**, where recency is not reliable or records tie.
   4. **Stable tiebreaker** (for example lowest record identifier) so reruns give the same result.
3. Log which record survived, which rule decided it, and why.

If the business requires a different order (for example recency before source trust), document and approve it.

Duplicate detection should run after format and category standardization (see Section 32.3) so that near-duplicates created by formatting differences are found.

---

# 6. Missing Data Handling Rules

## 6.1 Missingness Classification

Classify each missing value on two dimensions.

**Operational cause (why it is missing):**

- Not collected
- Not applicable
- Upstream failure
- Ingestion error
- Delayed arrival
- Business condition

**Statistical mechanism (how missingness relates to the data):**

- **MCAR**: missing completely at random, unrelated to any values
- **MAR**: missing at random, related to other observed values
- **MNAR**: missing not at random, related to the missing value itself

The statistical mechanism determines which imputation methods are defensible. Simple mean or median imputation is generally appropriate only under MCAR and still understates variance. MAR may justify model-based imputation. MNAR usually requires domain input or sensitivity analysis. If the mechanism cannot be established, do not impute, and flag instead.

## 6.2 Missing Value Actions

Rules:

- Do not impute values without understanding the reason for missingness.
- Use explicit "not applicable" categories where valid.
- Use "unknown" only when explicitly allowed.
- Avoid replacing missing values with zero unless zero is a valid business value.
- Avoid replacing missing values with mean or median unless statistically appropriate and documented.
- For critical fields, missing values should trigger rejection, quarantine, or manual review.
- Set an imputation flag on every imputed value.

## 6.3 Missingness Thresholds

Define thresholds such as:

- Columns with more than a defined percentage of missing values may be excluded.
- Rows with more than a defined percentage of missing required fields may be quarantined.
- Missingness above threshold should generate a data quality alert.

---

# 7. Invalid Value Handling Rules

## 7.1 Range Validation

For numeric fields:

- Define minimum valid value.
- Define maximum valid value.
- Detect impossible values.
- Detect negative values where only positive values are valid.
- Detect values outside business tolerance.

## 7.2 Categorical Validation

For categorical fields:

- Define an allowed value list.
- Detect misspellings.
- Detect case variations.
- Detect abbreviations.
- Detect obsolete categories.
- Map variants to canonical values only through an **approved mapping table** (see 11.1). "High confidence" is not enough on its own. A mapping is authorized when it appears in a mapping table that is versioned and approved by the data owner.
- Variants that match no approved mapping are flagged, not guessed.

## 7.3 Date Validation

For date fields:

- Detect impossible dates.
- Detect future dates where not allowed.
- Detect dates before collection began.
- Detect invalid date formats.
- Detect timezone ambiguity.
- Detect inconsistent start and end dates.
- Detect sentinel dates (for example 1900-01-01, 1970-01-01, 9999-12-31) and treat them under 8.6.

## 7.4 Relationship Validation

Rules:

- Validate foreign key relationships.
- Detect orphaned child records.
- Detect parent records without required children if applicable.
- Detect circular relationships if applicable.
- Detect invalid hierarchies.

---

# 8. Format Standardization Rules

## 8.1 Text Standardization

Rules:

- Remove leading and trailing whitespace.
- Collapse multiple internal spaces where appropriate.
- Standardize case for categorical fields.
- Preserve original values in audit fields when normalization changes meaning.
- Do not trim text fields where whitespace is meaningful unless documented.

## 8.2 Phone Numbers

Rules:

- Standardize to a consistent international format (E.164 is a common choice) or a documented national format.
- Remove invalid characters.
- Validate length and prefix.
- Flag invalid phone numbers instead of silently correcting them if correction is uncertain.

## 8.3 Email Addresses

Rules:

- Validate basic syntax.
- Lowercase the domain part, which is case-insensitive.
- The local part (before the @) is technically case-sensitive under the email standards, although nearly all providers treat it as case-insensitive. Lowercasing it is a convention for matching and deduplication, not a guarantee. Keep the original value in an audit field whenever you normalize it.
- Detect disposable domains if relevant.
- Detect role-based addresses if relevant.
- Flag invalid emails instead of deleting records unless required.

## 8.4 Postal Addresses

Rules:

- Standardize address components.
- Separate address lines, city, region, postal code, and country where possible.
- Validate postal codes against country rules.
- Detect missing country when multiple countries are possible.
- Use trusted address validation services where available.
- Store postal codes as text (see 3.3).

## 8.5 Identifiers

Rules:

- Preserve identifier case sensitivity if required.
- Remove surrounding whitespace.
- Preserve leading zeros and fixed lengths.
- Detect invalid identifier formats.
- Do not reassign identifiers.
- Maintain a mapping if identifiers are replaced or pseudonymized.

## 8.6 Sentinel and Placeholder Values

Many systems encode "missing" or "unknown" as ordinary-looking values. Examples: `-999`, `-1`, `0`, `9999`, `9999-12-31`, `1900-01-01`, `"N/A"`, `"NULL"`, `"none"`, `"unknown"`, `"TBD"`, `"."`, and whitespace-only strings.

Rules:

- Maintain a documented list of sentinel and placeholder values per source and field.
- Distinguish a true null, an empty string, and a placeholder string. Define in the contract which of these are equivalent for each field.
- Convert approved sentinels to explicit nulls (or an explicit "not applicable" or "unknown" category), and record the conversion in an audit field.
- Never include sentinel values in statistics, aggregations, or outlier detection.
- Treat unexpected sentinel-looking values (for example a spike of `-999`) as a data quality alert.

---

# 9. Date and Time Handling Rules

## 9.1 Timezone Policy

Rules:

- Define a canonical timezone for storage (UTC is a common choice).
- Preserve original timezone information when available.
- Convert timestamps to the canonical timezone only when business rules allow.
- Avoid mixing timezone-aware and timezone-naive timestamps.
- Use named timezones (for example IANA zone names), not fixed offsets, when local civil time matters, because offsets change with daylight saving time.
- Handle daylight saving edge cases explicitly:
  - **Ambiguous local times** occur when clocks fall back and one local time happens twice. Record which occurrence applies, or flag the record.
  - **Non-existent local times** occur when clocks spring forward and a local time is skipped. Flag or resolve by documented rule.
- Be explicit about whether a field is an instant in time (store in UTC) or a local wall-clock time such as a store opening hour or a birthday (store as local time with its zone or location).

## 9.2 Date Parsing

Rules:

- Define accepted date formats.
- Detect ambiguous formats (for example 03/04/2025 as day/month or month/day).
- Prefer explicit formats over inferred formats.
- Log records where date parsing fails.
- Quarantine records with critical unparseable dates at the point of failure, not in a later step.

## 9.3 Business Date Logic

Rules:

- Validate event date order.
- Validate that end date is not before start date.
- Detect future-dated records where not allowed.
- Detect stale records based on freshness rules.
- Detect records outside the expected analytical window.
- Use the pipeline's explicit as-of date (see 32.1), not the wall-clock run time, for all "future" and "stale" tests.

---

# 10. Numeric Data Handling Rules

## 10.1 Unit Consistency

Rules:

- Ensure numeric fields use the expected unit.
- Standardize units across sources.
- Document conversions.
- Avoid mixing currencies, weights, distances, or quantities without normalization.

## 10.2 Precision and Rounding

Rules:

- Preserve original precision where possible.
- Use exact decimal arithmetic for monetary values.
- Define rounding rules (including the rounding mode) for reporting.
- Avoid premature rounding.
- Record when rounding is applied.

## 10.3 Negative and Zero Values

Rules:

- Determine per field whether negative values are valid. Returns, adjustments, refunds, and credits are often legitimately negative.
- Determine whether zero is valid or indicates missingness.
- Flag negative values in fields where only positive values are expected.
- Do not convert negative values to positive automatically unless a rule is known.

## 10.4 Outliers

Rules:

- Detect statistical outliers using business-approved methods.
- Distinguish between valid rare events and invalid data.
- Do not remove outliers automatically unless they violate a business rule.
- Consider winsorizing, flagging, excluding, or separating outliers based on use case.
- Keep an outlier flag column if outliers are retained.
- Exclude sentinel values (8.6) before computing outlier thresholds.

---

# 11. Categorical Data Handling Rules

## 11.1 Canonical Categories

Rules:

- Define a master list of valid categories.
- Maintain a **versioned, approved mapping table** from variants (synonyms, abbreviations, misspellings, legacy values) to canonical categories. This table is the business approval referred to in 20.3.
- Map abbreviations only when unambiguous.
- Preserve original values in an audit field.
- Create an "other" or "unmapped" category only when necessary, and report its volume.

## 11.2 High Cardinality Fields

Rules:

- Identify categorical fields with excessive cardinality.
- Determine whether the field is truly categorical or an identifier.
- Consider grouping rare categories if appropriate for modeling.
- Avoid grouping categories for reporting without business approval.

## 11.3 Ordinal Fields

Rules:

- Identify ordinal categories.
- Preserve natural order.
- Do not treat ordinal values as simple numeric unless appropriate.
- Document ranking meaning.

---

# 12. Text Field Handling Rules

## 12.1 Free-Text Fields

Rules:

- Identify free-text fields.
- Detect language if relevant.
- Remove control characters where appropriate.
- Preserve meaningful punctuation if needed.
- Do not normalize text in ways that destroy meaning.

## 12.2 Sensitive Text

Rules:

- Scan for sensitive information.
- Mask, tokenize, or remove sensitive values.
- Prevent sensitive text from entering downstream systems without approval.

## 12.3 Comment and Note Fields

Rules:

- Separate structured and unstructured content where possible.
- Detect placeholder text.
- Detect test entries.
- Flag abusive or invalid content if relevant.
- Avoid deleting user-generated content without policy.

---

# 13. Consistency and Cross-Field Rules

## 13.1 Logical Consistency

Rules:

- Validate that dependent fields are logically consistent.
- Validate conditional requirements.
- Detect contradictions between related fields.
- Example areas:
  - Status and date fields
  - Age and date of birth
  - Country and currency
  - Product type and attributes
  - Start date and end date
  - Quantity and total amount

## 13.2 Calculated Field Validation

Rules:

- Validate derived fields against source fields.
- Detect calculation drift.
- Recompute derived fields when source values change.
- Store calculation logic metadata.

## 13.3 Status and Lifecycle Rules

Rules:

- Validate valid lifecycle transitions.
- Detect records stuck in invalid states.
- Detect impossible completion states.
- Detect records with missing timestamps for required lifecycle stages.

---

# 14. Referential Integrity Rules

## 14.1 Master Data Validation

Rules:

- Validate records against master data entities.
- Detect unmatched customers, products, locations, accounts, or vendors.
- Route unmatched records to a **suspense queue** (also called a suspense file) for resolution and reprocessing.
- Do not create fake master data records automatically.

## 14.2 Hierarchies

Rules:

- Validate parent-child relationships.
- Detect cycles.
- Detect orphaned children.
- Detect inactive parents with active children if invalid.
- Preserve historical hierarchy relationships where required.

## 14.3 Joins

Rules:

- Document join keys.
- Validate join cardinality.
- Detect unexpected fan-out.
- Detect unexpected row reduction.
- Log before-and-after row counts after every join.

---

# 15. Time-Series Specific Rules

If the dataset contains time-series data:

## 15.1 Timestamp Integrity

Rules:

- Validate timestamp uniqueness where required.
- Detect gaps in expected intervals.
- Detect duplicate timestamps.
- Detect out-of-order records.
- Detect irregular sampling.
- Check daylight saving transitions for duplicated or missing local-time intervals (see 9.1).

## 15.2 Windowing

Rules:

- Define valid time windows.
- Detect records outside the analysis window.
- Detect late-arriving data.
- Detect future-arriving data.

## 15.3 Seasonality and Trends

Rules:

- Identify sudden spikes or drops.
- Distinguish operational anomalies from data quality issues.
- Flag suspicious changes rather than auto-correcting.

---

# 16. Entity Resolution Rules

When records refer to the same real-world entity:

## 16.1 Matching Criteria

Define matching fields such as:

- Identifier
- Name
- Email
- Phone
- Address
- Date of birth
- Account number
- Tax ID
- Device ID

## 16.2 Match Confidence

Rules:

- Separate exact matches from fuzzy matches.
- Assign a confidence score.
- Auto-merge only high-confidence matches.
- Route medium-confidence matches to review.
- Preserve original entity records before merging.

## 16.3 Survivorship

Rules:

- Apply the same explicit, ordered survivorship logic defined in 5.3.
- Maintain merge history.
- Allow unmerge if errors are discovered.

---

# 17. Data Leakage Prevention Rules

For analytics and modeling pipelines:

## 17.1 Target Leakage

Rules:

- Remove fields that contain information from after the prediction point.
- Remove fields that directly reveal the target.
- Validate that features are available at the time of prediction.

## 17.2 Train/Test Contamination

Rules:

- Prevent duplicate records across training and validation sets.
- Prevent overlapping time windows.
- Prevent entity leakage across splits.
- Split data based on time, entity, or event where appropriate.

## 17.3 Derived Feature Safety

Rules:

- Document how each derived field is calculated.
- Ensure derived fields do not use future information.
- Version feature definitions.

## 17.4 Preprocessing Leakage

Rules:

- Split the data before fitting any learned preprocessing step.
- Fit imputers, scalers, encoders, outlier thresholds, category groupings, and feature selectors on the training set only, then apply the fitted transformation to validation and test sets.
- Within cross-validation, fit preprocessing inside each fold.
- Do not compute dataset-wide statistics (means, medians, quantiles, vocabularies) from data that includes the evaluation set.
- Note: this conflicts with generic "clean everything first" ordering. Deterministic, rule-based cleaning (formatting, sentinel conversion, validation) may run before the split. Statistically learned steps must run after it.

---

# 18. Privacy and Compliance Rules

## 18.1 Sensitive Data Identification

Identify:

- Names
- Email addresses
- Phone numbers
- Physical addresses
- Government identifiers
- Financial identifiers
- Health information
- Biometric data
- Location data
- Sensitive demographic data

This identification runs at intake, before profiling (see 4.0).

## 18.2 Protection Actions

Rules:

- Apply access controls.
- Mask sensitive fields.
- Tokenize identifiers.
- Pseudonymize where appropriate.
- Aggregate when individual-level detail is not required.
- Delete sensitive fields when not approved for use.
- **Pseudonymized and tokenized data is still personal data** under regimes such as GDPR, because it can be re-linked using additional information. It remains subject to access controls, purpose limits, retention limits, and deletion rights. Only data that is irreversibly anonymized, and that cannot reasonably be re-identified, falls outside those regimes. Do not label pseudonymized data as anonymous.
- Store re-identification keys and mapping tables separately from the pseudonymized data, with stricter access controls.
- Name the regimes in scope in the dataset's source registration (2.1) and apply their specific requirements (for example HIPAA identifiers, PCI DSS cardholder data rules).

## 18.3 Consent and Purpose

Rules:

- Record data consent status if applicable.
- Restrict usage to approved purposes.
- Prevent unauthorized downstream sharing.
- Maintain retention schedules.

## 18.4 Right to Deletion and Erasure

Rules:

- Support deletion and erasure requests where legally required, and complete them within the legally required timeframe (for example without undue delay under GDPR).
- Erasure applies to **all** layers that hold the data: raw zone, cleaned datasets, quarantine, rejection zone, audit and lineage records, backups (per backup retention policy), and derived datasets.
- Implement erasure through a documented mechanism compatible with immutable storage, such as:
  - Crypto-shredding (destroying the per-subject or per-partition encryption key).
  - Tombstoning the record and rebuilding affected versions.
  - Partitioning raw data so that affected partitions can be rewritten under controlled, audited exception.
- An approved erasure is an authorized exception to immutability (2.2, 27.1). It creates a new version and a deletion log entry. It must never be done by ad hoc editing.
- Where erasure cannot be completed in a layer (for example a legal hold or a legal retention duty), record the legal basis and the review date.
- Track deletion across derived datasets using lineage (Section 26). "Where feasible" is not an acceptable standard for datasets in lineage scope.
- Preserve deletion logs. Logs must record that an erasure happened without retaining the erased personal data.

---

# 19. Bias, Fairness, and Ethical Handling Rules

## 19.1 Protected Attributes

Rules:

- Identify protected or sensitive attributes.
- Determine whether they are required for fairness monitoring.
- Restrict their use in decision-making where prohibited.
- Prevent proxy discrimination where applicable.

## 19.2 Representation Checks

Rules:

- Assess coverage across segments.
- Detect underrepresented groups.
- Detect skewed missingness by segment.
- Flag datasets that may not represent the target population.

---

# 20. Data Transformation Rules

## 20.1 Allowed Transformations

Transformations are allowed only when:

- The business rule is documented.
- The transformation is deterministic.
- The original value can be preserved or audited.
- The downstream impact is understood.

## 20.2 Standard Transformations

Examples:

- Standardize units
- Standardize country codes
- Standardize currency codes
- Standardize date formats
- Standardize Boolean representations
- Normalize category names (via approved mapping tables, 11.1)
- Derive age from date of birth, calculated against the explicit as-of date (see 32.1), not the run date
- Derive duration from start and end timestamps
- Derive flags for missing, invalid, or outlier values

## 20.3 Prohibited Transformations

Do not:

- Invent missing values without approval.
- Convert invalid values to valid values without a rule.
- Silently delete records.
- Apply arbitrary rounding.
- Merge categories without business approval. An entry in an approved mapping table (11.1) counts as that approval.
- Change primary keys.
- Apply model-based imputation without governance.

---

# 21. Quarantine and Exception Handling Rules

## 21.1 Quarantine Queue

Records that fail critical record-level rules should be moved to a quarantine area, not deleted.

Quarantine should include:

- Original record
- Failed rule name
- Failure reason
- Source identifier
- Ingestion timestamp
- Severity level
- Suggested remediation

The quarantine area is subject to the same privacy, retention, and erasure rules as every other layer (Section 18).

## 21.2 Severity Levels

Severity is assessed at two scopes, which prevents one bad row from halting the whole pipeline.

**Record-level severity** (applies to individual records):

- **Critical:** The record cannot be used. Quarantine or reject the record. The pipeline continues.
- **High:** The record may be incorrect or incomplete. Flag it, and route to review if configured.
- **Medium:** The record is suspicious but usable with caution. Flag it.
- **Low:** Cosmetic or minor formatting issue. Log it.

**Dataset-level severity** (applies to the batch as a whole):

- **Critical (stop):** The dataset cannot be trusted or published. Examples: failed integrity check, schema contract breach, required columns missing, primary key uniqueness collapse, quarantine rate above its critical threshold, row count drop beyond tolerance. The pipeline stops.
- **High:** Alert and require approval to continue or publish.
- **Medium:** Warning.
- **Low:** Logged.

Rules:

- Define numeric thresholds that promote record-level problems to dataset-level severity (for example, if more than X% of records are quarantined for the same rule, the batch is dataset-level critical).
- The meaning of "critical" must always state its scope.

## 21.3 Exception Approval

Rules:

- Exceptions must be documented.
- Exceptions must have an owner.
- Exceptions must have an expiry date.
- Exceptions must be reviewed periodically.

---

# 22. Record Rejection Rules

Reject records only when:

- They violate a critical business rule.
- They cannot be corrected reliably.
- They pose a compliance risk.
- They fail primary key or required field validation.
- They are confirmed duplicates with no historical value.

Rejection requirements:

- Do not silently discard rejected records.
- Store rejected records in an audit or rejection zone.
- Record rejection reason.
- Allow reprocessing after correction.

---

# 23. Data Enrichment Rules

## 23.1 Internal Enrichment

Rules:

- Enrich only from approved internal reference data.
- Validate reference data freshness.
- **Pin and record the reference data version** used (see 32.1).
- Log enrichment source and timestamp.
- Do not overwrite original fields with enriched values unless approved.

## 23.2 External Enrichment

Rules:

- Validate external vendor data quality.
- Document licensing and usage rights.
- Record enrichment join success rate.
- Monitor enrichment drift.
- Pin and record the vendor data version or snapshot date.
- Avoid enriching sensitive fields without approval.

---

# 24. Aggregation Rules

## 24.1 Grain Definition

Rules:

- Define the grain before aggregation.
- Document grouping keys.
- Validate that aggregation does not hide important exceptions.
- Preserve pre-aggregation data where needed.

## 24.2 Aggregation Logic

Rules:

- Define how duplicates are handled before aggregation.
- Define how missing values and sentinel values affect totals and averages.
- Define whether distinct counts use exact or approximate logic.
- Define time bucket boundaries and the timezone used to form them.

## 24.3 Reconciliation

Rules:

- Compare totals before and after aggregation.
- Validate that no records are unintentionally excluded.
- Log row count differences.

---

# 25. Data Freshness and Timeliness Rules

## 25.1 Freshness Expectations

Define:

- Maximum acceptable data age.
- Expected delivery time.
- Acceptable delay by source.
- Business cutoff time.

## 25.2 Late Data

Rules:

- Detect late-arriving records.
- Decide whether late data is accepted.
- If accepted, record late arrival timestamp.
- If rejected, store in exception area.

## 25.3 Staleness Alerts

Rules:

- Alert if dataset is not refreshed within expected time.
- Alert if row count drops unexpectedly.
- Alert if source timestamps stop advancing.

---

# 26. Data Lineage Rules

For every dataset and transformation:

- Record source dataset.
- Record transformation name.
- Record transformation owner.
- Record execution timestamp.
- Record the **as-of date** used.
- Record input row count.
- Record output row count.
- Record rejected row count.
- Record quarantined row count.
- Record schema version.
- Record business rule version.
- Record versions of all reference data and mapping tables used.
- Record the pipeline code version.

Lineage must answer:

- Where did the data come from?
- What changes were made?
- Who approved the changes?
- When were the changes applied?
- What downstream assets depend on it?
- Which derived datasets contain data about a given subject (needed for erasure, 18.4)?

Lineage records must not retain erased personal data.

---

# 27. Versioning Rules

## 27.1 Dataset Versioning

Rules:

- Every published cleaned dataset must have a version.
- Versions are not edited in place once approved.
- Corrections create a new version, not an overwrite of history.
- The only permitted exception to retaining a prior version's content is an approved legal erasure (18.4), which is logged.
- Maintain version notes.

## 27.2 Rule Versioning

Rules:

- Every cleaning rule must have a version.
- Rule changes must be reviewed.
- Old rules must remain retrievable.
- Rule version must be stored with output metadata.
- Mapping tables, sentinel lists, and thresholds are versioned like rules.

## 27.3 Schema Versioning

Rules:

- Track schema changes over time.
- Distinguish additive, breaking, and deprecating changes.
- Notify downstream consumers of breaking changes.

---

# 28. Monitoring and Observability Rules

## 28.1 Quality Metrics

Monitor:

- Missing rate
- Invalid rate
- Duplicate rate
- Outlier rate
- Sentinel value rate
- Schema violation rate
- Freshness
- Row count
- Distinct count
- Orphan record rate
- Quarantine volume
- Rejection volume

## 28.2 Drift Monitoring

Monitor for:

- Sudden changes in row count
- Sudden changes in null rate
- New categories
- Missing categories
- Changed distributions
- Changed date ranges
- Changed identifier formats
- Changed source values
- Changed encoding

## 28.3 Alerting

Rules (severity as defined in 21.2):

- Dataset-level critical failures stop the pipeline.
- Record-level critical failures quarantine or reject the record and do not stop the pipeline unless a dataset-level threshold is crossed.
- High-severity issues generate alerts.
- Medium-severity issues generate warnings.
- Low-severity issues are logged.

---

# 29. Manual Review Rules

Some issues should not be fixed automatically.

Route to manual review when:

- Entity matching confidence is uncertain.
- Sensitive data is detected unexpectedly.
- Business rules conflict.
- High-volume outliers appear.
- Regulatory impact is possible.
- Data correction may affect financial reporting.
- Duplicate resolution is ambiguous.
- Missing critical fields require business interpretation.
- An erasure request conflicts with a legal retention duty.

Manual review requirements:

- Provide full context.
- Record reviewer identity.
- Record decision.
- Record reason.
- Apply decision consistently.

---

# 30. Output Dataset Rules

The final cleaned dataset must include:

- Standardized column names
- Approved data types
- Documented primary key
- Documented grain
- Data quality flags
- Processing timestamp (stored as metadata, excluded from reproducibility comparison, see 32.1)
- As-of date
- Dataset version
- Source identifier
- Schema version
- Rule version
- Quality summary
- Known limitations

## 30.1 Quality Flag Fields

Include flags such as:

- Missing critical fields
- Invalid format
- Outlier detected
- Sentinel value converted
- Duplicate resolved
- Imputed value used
- Quarantined record
- Manually corrected
- Late-arriving record
- Sensitive field masked

## 30.2 Metadata Bundle

Every output should be accompanied by:

- Data dictionary
- Row count
- Column count
- Quality report (including the before and after profile comparison, 4.3)
- Lineage information
- Freshness information
- Known exclusions
- Transformation summary
- Approval status

---

# 31. Approval and Governance Rules

## 31.1 Data Quality Ownership

Assign:

- Data owner
- Data steward
- Pipeline owner
- Quality rule owner
- Incident responder

## 31.2 Change Control

Rules:

- New cleaning rules require review.
- Rule modifications require approval.
- Emergency fixes require post-incident documentation.
- Business-facing definitions require sign-off.

## 31.3 Certification

Datasets may be marked as:

- Raw
- Cleaned
- Reviewed
- Certified
- Restricted
- Deprecated

Only certified datasets should be used for official reporting or regulated decisions.

---

# 32. Pipeline Execution Rules

## 32.1 Idempotency and Reproducibility

Rules:

- Rerunning the pipeline on the same input, the same rule versions, the same reference data versions, and the same as-of date must produce the same data output.
- Every run takes an explicit **as-of date** as a parameter. All date-relative logic (future-date checks, staleness checks, age derivation) uses it, never the wall-clock time.
- **Pin reference data**, enrichment sources, and mapping tables by version or snapshot. Record the versions in lineage.
- Keep non-deterministic metadata (processing timestamp, run identifier) separate from the data content, and exclude it when comparing outputs for reproducibility.
- Use stable ordering and fixed random seeds wherever order or randomness affects results (survivorship tiebreakers, sampling, splits).
- Processing must not create duplicate outputs.
- Partial failures must be recoverable.

## 32.2 Failure Handling

Rules:

- Stop on dataset-level critical failures.
- Continue past record-level failures only if they are quarantined, logged, and below dataset-level thresholds.
- Preserve failure details.
- Do not publish partial outputs unless explicitly approved.

## 32.3 Ordering

Recommended pipeline order:

1. Intake raw data and verify integrity (checksums, control totals) (2.5)
2. Register source and identify sensitive fields (2.1, 18.1)
3. Validate encoding and schema (3.1 to 3.5)
4. Quarantine structurally invalid rows (3.4)
5. Profile data, with sensitive-field protection (4.0 to 4.2)
6. Standardize formats: whitespace, case, encoding normalization, identifiers (8)
7. Convert approved sentinel values (8.6)
8. Parse and validate dates and numbers; quarantine critical parse failures here (7, 9.2)
9. Validate required fields and data types
10. Standardize categories using approved mapping tables (11.1)
11. Detect and resolve duplicates, using standardized values (5)
12. Validate business keys and referential integrity (7.4, 14)
13. Apply cross-field and lifecycle rules (13)
14. Handle missing values per Section 6
15. Detect outliers, excluding sentinels (10.4)
16. Entity resolution, if in scope (16)
17. Quarantine and reject exceptions, evaluate dataset-level thresholds (21, 22)
18. Apply enrichment using pinned reference data (23)
19. Apply derived fields using the as-of date (13.2, 20.2)
20. Apply privacy protections: masking, tokenization, pseudonymization (18.2)
21. Validate final grain and uniqueness
22. Re-profile the output and compare with the input profile (4.3)
23. Generate quality report and metadata bundle (30)
24. Write lineage record (26)
25. Publish the cleaned dataset

**Modeling pipelines only:** split the data (17.2) after step 9 and before step 14, and fit all learned preprocessing on the training portion only (17.4).

Lineage and logging happen continuously, not only at step 24. Every step records its input and output row counts.

## 32.4 Rule Testing

Rules:

- Every cleaning rule has automated tests: known-good inputs, known-bad inputs, and edge cases (nulls, empty strings, sentinels, daylight saving boundaries, leap days, non-ASCII text, very long values).
- Maintain a golden test dataset with expected outputs.
- Run the full test suite on every rule or pipeline change. Treat failures as blocking.
- Regression-test rule changes by running old and new rule versions on the same data and reviewing the differences in output (row counts, flag counts, changed values) before approval.
- Test the pipeline's failure paths: quarantine, dataset-level stop, and recovery after partial failure.
- Test erasure (18.4) end to end on non-production data.

---

# 33. Business Rule Examples

These are **illustrative, domain-specific examples** (mainly retail or order-management). They are not universal. Check each against the field-level rules in the data contract before adopting it. Define explicit rules such as:

- Customer records must have a unique customer identifier.
- Orders must have an order date.
- Order date cannot be in the future (relative to the as-of date) unless pre-order is allowed.
- Cancelled orders must have a cancellation date.
- Refunds cannot exceed original transaction amount.
- Product price cannot be negative.
- Email must be syntactically valid if provided.
- Country must be a valid ISO country code.
- Currency must be a valid ISO currency code.
- Date of birth must produce an age within a valid range.
- Start date must be before end date.
- Quantity on a **sales line** must be greater than zero. Return, adjustment, or inventory-correction records may legitimately carry negative or zero quantities, so apply this rule per record type.
- Status must belong to the approved status list.

---

# 34. Documentation Requirements

For every dataset, maintain:

- Dataset purpose
- Source description
- Field definitions
- Allowed values
- Sentinel and placeholder value list
- Cleaning rules
- Known limitations
- Quality thresholds
- Owner contact
- Change history
- Access restrictions
- Retention policy
- Regulatory scope

---

# 35. Final Cleaning Principles

1. Preserve raw data, and support lawful erasure when required.
2. Log every change.
3. Prefer flagging over silent correction.
4. Prefer quarantine over deletion.
5. Prefer deterministic rules over manual fixes.
6. Prefer business-approved definitions over assumptions.
7. Prefer reproducibility over one-time cleanup.
8. Prefer traceability over convenience.
9. Treat data quality as continuous, not one-time.
10. Do not clean data without understanding its business meaning.
11. Test the rules, not just the data.
12. Fit anything learned from data only on data you are allowed to learn from.

