#!/usr/bin/env python3
"""J24G97 O0: real r24 physical-prefix archival/trusted-head publication cuts.

No actual filesystem crash, shared durable transaction, or product safety proof.
"""
import argparse,io,json,pathlib,zipfile
from j24g96_trusted_head_oracle import ZIP_CASES,parse_chain,head,sha,require

def test(raw,name):
    current=parse_chain(raw);require(len(current)>=4,'genuine journal depth')
    old_end=current[-2]['pos']+68
    old_archive=raw[:old_end];prior=parse_chain(old_archive)
    require(len(prior)==len(current)-1,'real prefix generations')
    old_head=head(prior)[0];new_head=head(current)[0]
    require(old_head!=new_head,'distinct legitimate head roots')
    scenario=[
        ('prior_archive_prior_trusted_head',old_archive,old_head,True),
        ('latest_archive_latest_trusted_head',raw,new_head,True),
        ('latest_archive_stale_trusted_head',raw,old_head,False),
        ('prior_archive_future_trusted_head',old_archive,new_head,False),
    ]
    output={}
    for label,archive,trusted,expected in scenario:
        matches=(head(parse_chain(archive))[0]==trusted)
        require(matches is expected,'two-store split accepted')
        output[label]={'latest_head_matches_external_trust':matches,
                       'archive_bytes':len(archive)}
    require(head(parse_chain(old_archive))[0]==old_head,'prior ancestor recoverability')
    return {'source_file':name,'prior_file_bytes':old_end,'current_file_bytes':len(raw),
            'append_added_bytes':len(raw)-old_end,
            'prior_footer_count':len(prior),'current_footer_count':len(current),
            'prior_trusted_head':old_head.hex(),'current_trusted_head':new_head.hex(),
            'scenario_matrix':output,'stale_head_can_match_ancestor_prefix':True,
            'new_head_has_no_match_in_old_archive':True,
            'attacker_owned_external_head_allows_rollback_to_prior':True,
            'external_head_bytes_for_two_retained_epochs':64}

def main():
    p=argparse.ArgumentParser()
    for name in ZIP_CASES:p.add_argument('--'+name,required=True,type=pathlib.Path)
    p.add_argument('--output',required=True,type=pathlib.Path)
    args=p.parse_args();out={}
    for key,(zsha,source_head,files) in ZIP_CASES.items():
        zipped=getattr(args,key.replace('-','_')).read_bytes()
        require(sha(zipped).hex()==zsha,'original provider SHA')
        with zipfile.ZipFile(io.BytesIO(zipped)) as source:
            require(source.read('checkout-head.txt').decode().strip()==source_head,
                    'original source mismatch')
            for filename in files:
                out[key+'/'+filename]=test(source.read(filename),key+'/'+filename)
    require(len(out)==8,'expected eight histories')
    report={'schema':'cmpct-j24g97-real-prefix-archive-pin-crashcut-O0-v1',
            'results':out,'evidence_level':'O0, not actual crash fault injection or product durability',
            'decision':'SPLIT_DURABILITY_VETO_FOR_TRUSTED_HEAD_PUBLICATION'}
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'histories':len(out),'cross_pairings':sum(len(x['scenario_matrix']) for x in out.values()),
                      'inconsistent_pairings_rejected':sum(sum(not v['latest_head_matches_external_trust']
                                          for v in x['scenario_matrix'].values()) for x in out.values()),
                      'append_bytes_range':[min(x['append_added_bytes'] for x in out.values()),
                                            max(x['append_added_bytes'] for x in out.values())],
                      'result_SHA256':sha(args.output.read_bytes()).hex()},sort_keys=True))
if __name__=='__main__':main()
