"""JSON log of preprints: versions with change notes, journal submissions and the final published DOI."""
import datetime as dt
import json
import os
import re
import urllib.request

STATUSES = ("preprint", "submitted", "under review", "revision", "accepted", "published", "rejected", "withdrawn")


def parse_arxiv_version(feed_xml):
    """Latest version number from an arXiv API Atom response (the entry id ends in vN)."""
    m = re.search(r"<id>https?://arxiv\.org/abs/[^<]*?v(\d+)</id>", feed_xml)
    return int(m.group(1)) if m else None


def _fetch_arxiv(arxiv_id):
    url = "http://export.arxiv.org/api/query?id_list=%s" % arxiv_id
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "preprint-tracker/0.1"}), timeout=20) as r:
        return r.read().decode("utf-8")


class PreprintLog:
    def __init__(self, path="preprints.json", today=None):
        self.path = path
        self.today = today or dt.date.today()
        self.data = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                self.data = json.load(fh)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=1)

    def add(self, key, title, server="arXiv", identifier="", posted=None, note="initial version"):
        if key in self.data:
            raise ValueError("preprint %r already tracked" % key)
        posted = posted or self.today.isoformat()
        self.data[key] = {"title": title, "server": server, "id": identifier, "status": "preprint",
                          "versions": [{"v": 1, "date": posted, "note": note}], "history": [], "published_doi": ""}
        self.save()
        return self.data[key]

    def _get(self, key):
        if key not in self.data:
            raise KeyError("unknown preprint %r" % key)
        return self.data[key]

    def new_version(self, key, note, date=None):
        if not note.strip():
            raise ValueError("describe what changed in this version")
        p = self._get(key)
        v = p["versions"][-1]["v"] + 1
        p["versions"].append({"v": v, "date": date or self.today.isoformat(), "note": note})
        self.save()
        return v

    def set_status(self, key, status, venue="", note="", doi=""):
        if status not in STATUSES:
            raise ValueError("status must be one of: " + ", ".join(STATUSES))
        p = self._get(key)
        p["history"].append({"date": self.today.isoformat(), "status": status, "venue": venue, "note": note})
        p["status"] = status
        if status == "published":
            if not re.match(r"10\.\d{4,9}/\S+$", doi or ""):
                raise ValueError("published status needs the journal DOI")
            p["published_doi"] = doi
        self.save()

    def days_in_status(self, key):
        p = self._get(key)
        last = p["history"][-1]["date"] if p["history"] else p["versions"][0]["date"]
        return (self.today - dt.date.fromisoformat(last)).days

    def check_remote(self, key, fetch=_fetch_arxiv):
        """Compare the latest arXiv version with the log; returns (remote_version, local_version)."""
        p = self._get(key)
        if p["server"].lower() != "arxiv" or not p["id"]:
            raise ValueError("remote check is only available for arXiv preprints with an id")
        return parse_arxiv_version(fetch(p["id"])), p["versions"][-1]["v"]

    def needs_attention(self, stale_days=90):
        """Preprints whose journal version is published but not linked, or that sit too long in one status."""
        out = []
        for k, p in self.data.items():
            if p["status"] in ("submitted", "under review", "revision") and self.days_in_status(k) > stale_days:
                out.append((k, "%s for %d days" % (p["status"], self.days_in_status(k))))
            if p["status"] == "accepted":
                out.append((k, "accepted: update the preprint with the journal reference once published"))
            if p["status"] == "rejected":
                out.append((k, "rejected: choose the next venue"))
        return out

    def changelog(self, key):
        p = self._get(key)
        lines = ["# %s" % p["title"], "", "%s %s - status: **%s**%s" % (
            p["server"], p["id"], p["status"], " (published: https://doi.org/%s)" % p["published_doi"] if p["published_doi"] else ""),
                 "", "## Versions", ""]
        lines += ["- **v%d** (%s): %s" % (v["v"], v["date"], v["note"]) for v in p["versions"]]
        if p["history"]:
            lines += ["", "## Publication history", ""]
            lines += ["- %s: %s%s%s" % (h["date"], h["status"], " at %s" % h["venue"] if h["venue"] else "",
                                         " (%s)" % h["note"] if h["note"] else "") for h in p["history"]]
        return "\n".join(lines) + "\n"
