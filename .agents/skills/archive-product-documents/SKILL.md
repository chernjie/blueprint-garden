---
name: archive-product-documents
description: Create minimal product-document archive entries from official product metadata, then later find, verify, download, name, and record publicly available PDF product manuals and care documents in this repository.
---

# Archive Product Documents

Create one flat, self-contained archive entry per product model under
`docs/items/`. Store only information and documents already available to the
public. Never add receipts, serial numbers, account data, access codes, private
photos, addresses, or user-specific installation details.

## Two-stage workflow

### Stage 1: intake from ChatGPT

Use this mode when the user supplies a brand and model and wants the archive
entry created immediately without downloading PDFs.

1. Identify the product with at least brand and model.
2. Find an official manufacturer product page.
3. Determine these values from official sources:
   - brand;
   - manufacturer;
   - model;
   - product name;
   - product page URL.
4. Invoke the authoritative skeleton renderer:

```bash
python3 .agents/skills/archive-product-documents/scripts/create_pending_entry.py \
  --brand '<brand>' \
  --manufacturer '<manufacturer>' \
  --model '<model>' \
  --name '<product name>' \
  --product-page '<official product page URL>'
```

5. Commit the generated `README.md` and `item.toml`.

The renderer is the only authority for creating initial archive files. Do not
construct `item.toml` or `README.md` manually in the skill.

During intake:

- do not download PDFs;
- do not compute hashes, file sizes, page counts, or document filenames;
- do not add placeholder `[[documents]]` tables;
- omit unknown optional metadata rather than guessing.

An entry without `[[documents]]` is intentionally incomplete and may fail the
full archive validator until Stage 2 is complete.

### Stage 2: completion with Codex

Use this mode when asked to complete pending product-document archives.

1. Run:

```bash
python3 .agents/skills/archive-product-documents/scripts/complete_pending_entry.py
```

The script reports every `docs/items/*/item.toml` that lacks a non-empty
`[[documents]]` array. A specific entry may also be passed directly.

2. For each reported entry, search the web with quoted identifiers. Search the
   exact model first, then combine it with terms such as `manual`,
   `instructions`, `use and care`, `installation`, `service`, and retailer item
   numbers when available.
3. Prefer sources in this order:
   - manufacturer or brand website;
   - retailer product or support website;
   - reputable public manual archive or mirror.
4. Open each candidate and verify the document itself contains the expected
   brand/model or another strong combination of identifiers. Do not rely only on
   a search-result title. Reject near matches and undocumented model families.
5. Compare candidates with documents already archived for the model. Treat files
   as equivalent when their identifiers, title, sections, page count, and text
   match, even if optimization changes the file hash. Keep one copy, preferring
   manufacturer sources, then retailer originals, then mirrors. Replace a
   lower-authority or lower-quality copy and update its existing metadata record;
   do not add a duplicate document entry.
6. Preserve a combined document as one file. Do not split, merge, convert, or
   relabel documents in ways that imply content the source does not contain.
7. Download verified PDFs with `scripts/download_pdf.py`. Record the public asset
   URL, publishing page, retrieval date, source type, SHA-256 digest, file size,
   title, document type, and languages in `item.toml`.
   - If an otherwise public source blocks automated retrieval, report the exact
     URL and normalized target filename. Ask the user to download it manually,
     then verify and archive that local file. Do not bypass access controls or
     replace the document with an unofficial reconstruction.
8. Update `README.md` as a concise human-readable record linking every local
   document and its public source.
9. Run `scripts/validate_entry.py` on the completed entry. Resolve every error
   before finishing. Report documents that could not be found; never fabricate
   placeholders.

## Entry Layout

Use this exact shape:

```text
docs/items/<brand>-<model>/
├── item.toml
├── README.md
└── documents/
    └── <brand>-<model>-<document-type>[-<revision>]-<languages>.pdf
```

Normalize path components to lowercase ASCII kebab-case. Remove punctuation
except meaningful model hyphens. Use the canonical public brand spelling for
metadata and a compact brand slug for paths. For example, `TrueWellness` model
`52913-BLK` becomes `truewellness-52913-blk`.

## Document Naming

Name every document:

```text
<brand>-<model>-<document-type>[-<revision>]-<languages>.pdf
```

Use a specific document type taken from the document itself when possible:

- `user-manual`
- `use-and-care-instructions`
- `installation-instructions`
- `assembly-instructions`
- `service-manual`
- `quick-start-guide`
- `parts-diagram`
- `specification-sheet`
- `warranty`
- `safety-data-sheet`

Use lowercase ISO 639-1 language codes joined by hyphens in document order, such
as `en`, `en-fr`, or `en-fr-es`. Omit the language suffix only when the document
contains no meaningful written language.

When two distinct documents would receive the same name, set `revision` to a
lowercase kebab-case source revision or publication date found inside the
document and insert it before the languages. Do not use the download date to
invent a document version.

## Metadata

Write `item.toml` as the authoritative structured record. A completed entry
requires `schema_version`, `name`, `brand`, `model`, and at least one `documents`
entry. A Stage 1 intake entry intentionally omits `documents` until Codex
completes it. Optional product fields are `manufacturer`, `item_numbers`, `upcs`,
`product_url`, and `support_url`. Omit unknown optional values rather than
guessing.

Require each completed document to contain `title`, `type`, `file`, `languages`,
`source_url`, `source_type`, `retrieved`, `sha256`, and `bytes`. Optional document
fields are `source_page_url`, `source_filename`, `resolved_url`, `revision`, and
`pages`.

```toml
schema_version = 1
name = "Product name"
brand = "Canonical brand"
manufacturer = "Manufacturer, when different"
model = "MODEL"
item_numbers = ["RETAILER-ID"]
upcs = ["012345678905"]
product_url = "https://public-product-page.example"
support_url = "https://public-support-page.example"

[[documents]]
title = "Title printed in document"
type = "use-and-care-instructions"
file = "documents/brand-model-use-and-care-instructions-en.pdf"
languages = ["en"]
source_url = "https://public-source.example/manual.pdf"
source_page_url = "https://retailer.example/product"
source_filename = "Original Manual.pdf"
source_type = "manufacturer"
retrieved = 2026-01-31
sha256 = "lowercase hex digest"
bytes = 12345
pages = 12
```

Allowed `source_type` values are `manufacturer`, `retailer`, and
`third-party-mirror`. Classify the publisher identified by `source_page_url`, not
the CDN hosting `source_url`. If using a mirror, explain in `README.md` which
official or retailer page confirmed the product identity and why no first-party
download was available.

## Downloading PDFs

Use Python 3.11 or newer and run:

```bash
python3 .agents/skills/archive-product-documents/scripts/download_pdf.py \
  --url '<verified-pdf-url>' \
  --referer '<publishing-page-url>' \
  --output 'docs/items/<entry>/documents/<normalized-name>.pdf'
```

The script rejects non-HTTP URLs, non-public hosts, private-network redirects,
non-PDF responses, oversized files, and silent overwrites. Record `resolved_url`
when the script reports a stable final URL different from `source_url`. Use
`--replace` only when a verified upstream document changed and record that change
in the entry.

For a manually downloaded file, move it to the normalized target path, verify
the PDF signature, page count, exact product identifiers, byte size, and SHA-256
digest, then record the same provenance fields as an automated download.

## Validating Entries

Run:

```bash
python3 .agents/skills/archive-product-documents/scripts/validate_entry.py \
  docs/items/<entry>
```

The validator checks the schema, naming convention, path safety, source fields,
README links, PDF signatures, byte counts, hashes, duplicate content, and orphaned
PDF files. It checks page counts when `pdfinfo` is installed.

## Public-Archive Boundary

Archive vendor-authored documents and public product facts. Link the original
public product and document pages. Do not claim that public availability grants a
redistribution license; preserve source and authorship information so a document
can be removed or replaced by a link if needed.
