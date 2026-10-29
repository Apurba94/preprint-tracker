# preprint-tracker

**Keep track of your preprints: every version with what changed, where each paper was submitted
and when, how long it has been under review, and the final journal DOI.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Preprints on arXiv, bioRxiv, medRxiv or OSF go through several versions and journal submissions.
Months later it is hard to remember which version corresponds to which submission, what changed in
v3, or whether the preprint was ever linked to the published article (an often-forgotten step that
splits citations). A small log answers these questions and reminds you of loose ends.

## Features

- Preprints with server, identifier, posting date; versions with mandatory change notes
- Status history: preprint, submitted, under review, revision, accepted, published (with DOI), rejected, withdrawn
- Days in the current status; `attention` lists long reviews, accepted papers to link, rejected papers to resubmit
- `check` compares the latest arXiv version (via the arXiv API) with your log
- Markdown changelog per preprint, e.g. for the version comments field or a lab wiki

## Usage

```bash
pip install .
preprint-tracker add soil-drought "Drought reshapes soil microbes" --id 2401.01234 --posted 2026-01-02
preprint-tracker version soil-drought "Added second field season; new Fig. 4"
preprint-tracker status soil-drought submitted --venue "Soil Biology Journal"
preprint-tracker status soil-drought published --doi 10.1000/sbj.2026.123
preprint-tracker list
preprint-tracker attention
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
