#!/usr/bin/env python3
"""O200 held-out replication: fixed-sample CDC admission cannot see masked structural change.

Explicitly disclosed pilot in frozen preregistration. This is an exact C source research
proxy with fully charged zlib6 chunks; no Builder, packaging or product credit.
"""
from __future__ import annotations
import hashlib, json, platform, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
from o197_native_cdc_mutation_court import authenticate_and_compile, SOURCE_BLOB
from o198_cdc_codec_aware_oracle import corpus, measure, SIZE
from o199_cdc_pair_admission_court import detector, mutate
SEEDS=(811,812,813)
MODES=("fixed256","fixed512","fixed1024","native")


def camouflage(original: bytes) -> bytes:
    mask=bytearray(len(original))
    # EXACT O199 sampled windows, no changes to O199 detector or thresholds.
    for i in range(12):
        pos=int((i+0.5)*len(original)/12)-2048
        pos=min(max(pos,0),len(original)-4096)
        mask[pos:pos+4096]=original[pos:pos+4096]
    for quarter in (1,2,3):
        pos=min(len(original)*quarter//4,len(original)-64)
        mask[pos:pos+64]=original[pos:pos+64]
    return bytes(mask)


def main():
    t=time.time()
    rows=[]
    with tempfile.TemporaryDirectory(prefix="o200-native-") as tmp:
        lib,compiler=authenticate_and_compile(ROOT,Path(tmp)/"cdc.so")
        for seed in SEEDS:
            random_base=corpus("entropy",seed)
            masked_base=camouflage(random_base)
            for edit in ("shift1","shift256"):
                pair=[]
                for label,base in (("random_original",random_base),("masked_sparse",masked_base)):
                    modified=mutate(base,SIZE//3,edit)
                    detect=detector(base,modified)
                    costs={m:measure(base,modified,m,lib) for m in MODES}
                    fixed=min(MODES[:-1],key=lambda m:costs[m]["charged_storage_proxy_bytes"])
                    saved=costs[fixed]["charged_storage_proxy_bytes"]-costs["native"]["charged_storage_proxy_bytes"]
                    row={
                      "seed":seed,"edit":edit,"body":label,
                      "base_sha256":hashlib.sha256(base).hexdigest(),
                      "variant_sha256":hashlib.sha256(modified).hexdigest(),
                      "detector":detect,"best_fixed_hindsight":fixed,
                      "native_minus_best_fixed_bytes":-saved,
                      "native_saving_percent":round(100*saved/costs[fixed]["charged_storage_proxy_bytes"],6),
                      "modes":costs,
                    }
                    assert all(x["exact_reassembly"] for x in costs.values())
                    pair.append(row);rows.append(row)
                a,b=pair
                assert a["detector"]["anchor_displacements"]==b["detector"]["anchor_displacements"],"probe displacement changed"
                assert a["detector"]["sample_zlib_ratio"]==b["detector"]["sample_zlib_ratio"],"sample ratio changed"
                assert a["detector"]["admit"]==b["detector"]["admit"],"detector decision changed"
    original=[x for x in rows if x["body"]=="random_original"]
    masked=[x for x in rows if x["body"]=="masked_sparse"]
    n_masked_losses=sum(x["native_minus_best_fixed_bytes"]>0 and x["detector"]["admit"] for x in masked)
    n_orig_wins=sum(x["native_minus_best_fixed_bytes"]<0 and x["detector"]["admit"] for x in original)
    recap={
        "heldout_pairs":6,"paired_observations":12,
        "identical_detector_output_pairs":6,
        "original_native_wins":n_orig_wins,
        "masked_native_losses_while_admitted":n_masked_losses,
        "prediction_met":n_masked_losses>=4 and n_orig_wins>=4,
        "decision":"REPLICATED_SAMPLING_NONIDENTIFIABILITY" if n_masked_losses>=4 and n_orig_wins>=4 else "REPLICATION_NOT_CONFIRMED",
    }
    result={
      "schema":"cmpct-o200-heldout-sample-blindspot-v1",
      "source_native_git_blob":SOURCE_BLOB,
      "source_parent_prereg_commit":"24a1b76fa3b7bbefac9e36025434824faf001105",
      "seeds":SEEDS,"edits":["shift1","shift256"],"insertion_position":SIZE//3,
      "research_only":True,"complete_product_economics_unmeasured":True,
      "compiler":compiler,"host":platform.platform(),"elapsed_wall_s":round(time.time()-t,3),
      "recap":recap,"observations":rows,
    }
    out=ROOT/"o200-evidence";out.mkdir(exist_ok=True)
    (out/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    print("O200_RECAP="+json.dumps(recap,sort_keys=True))
    print("O200_EXACT_REASSEMBLY_AND_IDENTICAL_OBSERVABLES=PASS")
    print("O200_PRODUCT_GATE=UNMEASURED")


if __name__=="__main__":
    main()
