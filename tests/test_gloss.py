"""The glossing run: what is sent, what is accepted back, what it is keyed on.

None of this calls the API. The three things worth pinning are that the
model is never allowed to invent Portuguese, that a change to the prompt or
to the model invalidates the cached responses, and that the dry-run sample
is the one config.yaml describes.
"""

from __future__ import annotations

import json

import pytest

from scripts import gloss


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    """A handful of rows in the shape load_rows() produces."""
    def row(rank, lemma, pos, mwe=False, split=False, share=1.0):
        return {"rank": rank, "lemma": lemma, "pos": pos, "is_mwe": mwe,
                "raw_freq": 10 ** 6 // rank, "freq_per_million": f"{1000 / rank:.3f}",
                "split": split, "pos_share": share}
    return [row(1, "ser", "verb"), row(2, "meia", "noun", split=True, share=0.6),
            row(3, "bom dia", "mwe", mwe=True), row(4, "casa", "noun")]


# -- the prompt --------------------------------------------------------------


def test_prompt_header_is_not_sent(release_cfg):
    """scripts/gloss_prompt.md explains itself above the rule; only what is
    below the rule is the prompt."""
    text = gloss.system_prompt(release_cfg)
    assert "version\ncontrolled" not in text and "strips this header" not in text
    assert text.startswith("You are compiling English glosses")
    assert "copied exactly" in text


def test_prompt_forbids_inventing_portuguese(release_cfg):
    text = gloss.system_prompt(release_cfg)
    assert "Do not write a sentence of your own" in text
    assert "empty string" in text          # the escape hatch when nothing fits


# -- the request -------------------------------------------------------------


def test_request_pins_model_and_limits(release_cfg, rows):
    p = gloss.request_params(release_cfg, "PROMPT", rows[0], ["Vou ser breve."])
    assert p["model"] == release_cfg["gloss"]["model"] == "claude-opus-5"
    assert p["max_tokens"] == release_cfg["gloss"]["max_tokens"]
    assert p["output_config"]["effort"] == release_cfg["gloss"]["effort"]
    assert p["output_config"]["format"]["schema"]["additionalProperties"] is False
    # No temperature: the parameter does not exist on this model family.
    assert "temperature" not in p


def test_split_rows_are_told_their_share(release_cfg, rows):
    block = gloss.user_block(rows[1], ["As meias estão no chão."])
    assert "60%" in block and "other reading" in block
    assert "share:" not in gloss.user_block(rows[3], ["Vamos para casa."])


def test_a_row_with_no_sentences_says_so(release_cfg, rows):
    block = gloss.user_block(rows[3], [])
    assert "none available" in block and "leave" in block


# -- the cache ---------------------------------------------------------------


def test_cache_key_follows_lemma_and_pos(release_cfg, rows):
    a = gloss.cache_file(release_cfg, rows[3])
    b = gloss.cache_file(release_cfg, dict(rows[3], pos="verb"))
    assert a != b
    assert a.name.startswith("casa__noun-") and a.parent.name == "gloss"


@pytest.mark.parametrize("change", [
    {"model": "claude-opus-4-8"}, {"max_tokens": 4000}, {"effort": "high"},
    {"thinking": "disabled"},
])
def test_changing_the_run_invalidates_the_cache(release_cfg, rows, change):
    """A cached response is only reused for the exact run that produced it."""
    from scripts import config as config_mod

    base = gloss.stamp_for(release_cfg, "pd", rows[0], ["Vou ser breve."])
    other = config_mod.with_overrides(
        release_cfg, {f"gloss.{k}": v for k, v in change.items()})
    assert gloss.stamp_for(other, "pd", rows[0], ["Vou ser breve."]) != base


def test_changing_the_prompt_or_the_sentences_invalidates_the_cache(release_cfg, rows):
    base = gloss.stamp_for(release_cfg, "pd", rows[0], ["Vou ser breve."])
    assert gloss.stamp_for(release_cfg, "OTHER", rows[0], ["Vou ser breve."]) != base
    assert gloss.stamp_for(release_cfg, "pd", rows[0], ["Serei breve."]) != base


# -- what comes back ---------------------------------------------------------

SENT = ["Vou ser breve.", "Não quero ser mau."]


def _reply(**kw):
    out = {"gloss": "to be", "example_pt": SENT[0], "example_en": "I'll be brief.",
           "flags": []}
    out.update(kw)
    return out


def test_a_good_reply_passes():
    assert gloss.verify(_reply(), SENT) == ""


def test_an_invented_example_is_rejected():
    """The whole point: every example sentence is a real corpus line."""
    assert "not one of the sentences" in gloss.verify(
        _reply(example_pt="Eu sou português."), SENT)


def test_an_edited_example_is_rejected():
    """Even a corrected or re-punctuated line is not the line we sent."""
    assert gloss.verify(_reply(example_pt="Vou ser breve"), SENT)


def test_no_example_is_allowed():
    """Better an entry with no example than a wrong one."""
    assert gloss.verify(_reply(example_pt="", example_en=""), SENT) == ""


def test_an_untranslated_example_is_rejected():
    assert gloss.verify(_reply(example_en=""), SENT)


def test_an_empty_gloss_is_rejected():
    assert gloss.verify(_reply(gloss="  "), SENT)


def test_unknown_flags_are_rejected():
    assert "unknown flag" in gloss.verify(_reply(flags=["rude"]), SENT)
    assert gloss.verify(_reply(flags=["vulgar", "bp-leaning"]), SENT) == ""


class _Block:
    def __init__(self, text): self.type, self.text = "text", text


class _Response:
    def __init__(self, text, stop="end_turn"):
        self.content, self.stop_reason, self.stop_details = [_Block(text)], stop, None


def test_truncated_replies_are_flagged_not_guessed():
    parsed = gloss.parse_reply(_Response('{"gloss":"to b', stop="max_tokens"))
    assert parsed["error"] and parsed["flags"] == ["uncertain"]
    assert gloss.verify(parsed, SENT)


def test_a_refusal_becomes_a_review_row():
    parsed = gloss.parse_reply(_Response("", stop="refusal"))
    assert "refusal" in parsed["error"]


def test_missing_fields_are_filled_in_not_crashed_on():
    parsed = gloss.parse_reply(_Response(json.dumps({"gloss": "to be"})))
    assert parsed["example_pt"] == "" and parsed["flags"] == []


# -- the dry-run sample ------------------------------------------------------


def test_dryrun_sample_matches_the_config(release_cfg):
    """Deterministic, stratified, and containing the awkward cases."""
    d = release_cfg["gloss"]["dryrun"]
    rows = gloss.load_rows(release_cfg)
    sample = gloss.dryrun_sample(release_cfg, rows)
    assert len(sample) == sum(n for _, _, n in d["strata"])
    for lo, hi, n in d["strata"]:
        assert sum(lo <= r["rank"] <= hi for r in sample) == n
    assert [r["rank"] for r in sample] == sorted(r["rank"] for r in sample)
    assert sum(r["split"] for r in sample) >= d["require"]["multi_pos"]
    assert sum(r["is_mwe"] for r in sample) >= d["require"]["mwe"]
    feminine = gloss.kept_feminine_nouns(release_cfg)
    assert sum(r["pos"] == "noun" and r["lemma"] in feminine
               for r in sample) >= d["require"]["kept_feminine_nouns"]
    assert sample == gloss.dryrun_sample(release_cfg, rows)
