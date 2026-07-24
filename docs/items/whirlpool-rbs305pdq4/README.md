# Whirlpool RBS305PDQ4

30-inch electric single built-in wall oven.

## Product identification

- Brand: Whirlpool
- Model: `RBS305PDQ4`
- Product type: electric single built-in wall oven
- Supply: 120/208 V or 120/240 V, 60 Hz

The appliance serial number and household-specific installation details are intentionally excluded from this public repository.

## Public product and parts references

- [Whirlpool owner-center page for the RBS305PDQ model family](https://www.whirlpool.com/owners-center-pdp.RBS305PDQ.html)
- [Whirlpool manuals and literature lookup](https://homedelivery.whirlpoolcorp.com/services/manuals.html)
- [WhirlpoolParts model-specific parts catalog](https://www.whirlpoolparts.com/Shop-For-Parts/a13b5d113250/Model-RBS305PDQ4-Whirlpool-Range-Stove-Oven-Parts)
- [PartSelect RBD305PDQ4 parts catalog](https://www.partselect.com/Models/RBD305PDQ4/)

> The PartSelect link is for model `RBD305PDQ4`, which is a different model identifier. It is retained only as a nearby-family research lead and must not be treated as proof that a listed part fits `RBS305PDQ4`.

## Known control component

The model-specific WhirlpoolParts catalog identifies the electronic control board as Whirlpool OEM part `4448874` and reports it as no longer available. This is useful maintenance evidence, but any substitute or rebuilt board still requires fitment verification against the exact oven model.

## Verified public documents

### Use & Care Guide

- Title: **Built-In Electric Oven Use & Care Guide**
- Whirlpool document number: `8300772B`
- Models listed in the document include `RBS305`
- Pages: 16
- Languages: English
- Source: [Whirlpool PDF](https://www.whirlpool.com/content/dam/global/documents/200210/owners-manual-8300772-RevB.pdf)

This is a model-family manual rather than a suffix-specific document, but it explicitly lists `RBS305`, making it applicable to model `RBS305PDQ4` unless a suffix-specific revision states otherwise.

### Dimension Guide

- Title: **30-inch Electric Built-in Single and Double Ovens Dimension Guide**
- Whirlpool reference: `8300654`
- Revision date printed in document: `2003-02-26`
- Product series listed in the document include `RBS305PD`
- Pages: 1
- Languages: English
- Source: [Whirlpool PDF](https://www.whirlpool.com/content/dam/global/documents/200302/dimension-guide-8300654-D-WH.pdf)

The dimension guide states that these ovens require a three-wire or four-wire, single-phase, 240-volt, 60 Hz AC supply. Models rated at 7.2 kW or below at 240 V use a separate 30 A circuit; higher-rated models in the guide use a 40 A circuit. Confirm the exact appliance nameplate rating before sizing or modifying a circuit.

## Archive status

Both documents are verified as public Whirlpool-authored PDFs and are linked above. Their binary files have not yet been mirrored into `documents/`, because the current repository connector cannot ingest the PDF bytes from external URLs. Consequently, `item.toml` is intentionally deferred: the archive validator requires local PDFs plus exact byte counts and SHA-256 hashes.

Normalized target filenames for a future binary import:

- `documents/whirlpool-rbs305pdq4-use-and-care-instructions-revb-en.pdf`
- `documents/whirlpool-rbs305pdq4-dimension-guide-8300654-en.pdf`

Once the files are downloaded into those paths, generate their hashes and byte counts, add `item.toml`, and run:

```bash
python3 .agents/skills/archive-product-documents/scripts/validate_entry.py \
  docs/items/whirlpool-rbs305pdq4
```
