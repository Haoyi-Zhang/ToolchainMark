"""Reconstruct owned-object scientific aggregates from retained raw rows.

Pure data checks only: this module never compiles, loads or executes an object.
"""
from collections import Counter
import math
import hashlib
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from owned_native_tool import tool

INPUTS = [0, 1, 5, 13, 144, 99991]
P1, P2 = '4d6f7270682d3031', '5365636f6e642d32'
SHAPES = {'MR01':(1,1,0), 'MR02':(2,0,12), 'MR03':(1,1,0),
          'MR04':(1,2,0), 'MR05':(2,2,0), 'MR08':(1,2,12),
          'MR09':(1,2,0), 'MR10':(1,2,0), 'MR13':(2,3,0), 'MR14':(2,2,0)}

VERDICTS={'SATISFIED','INCONSISTENT','INADMISSIBLE'}

def require(condition,message):
    if not condition:raise ValueError(message)


def validate_row(row):
    """Bind the finite owned action plan to raw bytes/calls, not supplied sums.

    Historical LLVM IR is compared as text; it is never imported, compiled or
    executed. Accepted record consistency is not execution authentication.
    """
    identity = row['identity']
    require(type(identity) is list and len(identity)==7, 'invalid owned identity')
    family,variant,profile,cohort,relation,mode,bypass = identity
    require(family in tool.FAMILIES and type(variant) is int and 0<=variant<4
            and profile in tool.PROFILES and type(bypass) is bool, 'invalid owned context')
    require(cohort in {'clean-workflow','integrity-challenge'} and relation in SHAPES,
            'unknown owned action plan')
    require((cohort=='clean-workflow' and mode=='checksum' and bypass is False)
            or (cohort=='integrity-challenge' and relation=='MR10'
                and mode in {'checksum','none','payload','both','outside','restore'}), 'invalid owned intervention')
    shape = SHAPES[relation]
    if relation=='MR10' and mode in {'none','payload','both','outside'}:
        shape=(1,1,0)
    for name,count in zip(('builds','extractions','host_calls'),shape):
        require(type(row[name]) is list and len(row[name])==count, 'owned action evidence missing: '+name)
    facts=row['admission']
    require(type(facts) is dict and {'subject_exists','isolated_workspace'}<=facts.keys()
            and all(type(v) is bool for v in facts.values()),'invalid owned admission')
    require(type(row['observations']) is dict, 'invalid owned observations')
    expected_verdict = ('INADMISSIBLE' if relation=='MR10' and mode!='checksum' else
                        'INCONSISTENT' if bypass else 'SATISFIED')
    require(row['verdict']==expected_verdict,'owned verdict contradicts fixed action plan')
    if expected_verdict!='INADMISSIBLE':
        require(all(v is True for v in facts.values()), 'owned admitted premise is false')
    objects=[]
    for index,build in enumerate(row['builds']):
        require(build['family']==family and type(build['variant']) is int and build['variant']==variant
                and build['requested_compiler']==build['actual_compiler']=='llvmlite'
                and build['requested_profile']==build['actual_profile']==profile,
                'owned build context differs')
        marked=not (relation=='MR03' or (relation=='MR02' and index==0))
        payload=P2 if relation in {'MR05','MR13'} and index==1 else P1
        require(type(build['marked']) is bool and build['marked']==marked
                and build['key']=='key-alpha' and build['payload_hex']==payload, 'owned build request differs')
        require(type(build['object_hex']) is str, 'invalid owned object bytes')
        raw=bytes.fromhex(build['object_hex'])
        require(raw.hex()==build['object_hex'] and hashlib.sha256(raw).hexdigest()==build['object_sha256'],
                'owned object identity differs')
        tool.elf_sections(raw)
        require(build['source']==tool.llvm_source(family,variant,bytes.fromhex(payload) if marked else None,
                                                 'key-alpha','x86_64-pc-windows-msvc'),
                'owned source text differs from request')
        require(build['native_inputs']==INPUTS and all(type(x) is int for x in build['native_inputs']),
                'owned native input frame differs')
        reference=[tool.expected(family,variant,x) for x in INPUTS]
        for name in ('native_outputs','reference_outputs'):
            require(type(build[name]) is list and all(type(x) is int for x in build[name])
                    and build[name]==reference, 'owned output/reference differs')
        if marked:
            require(tool.extract(raw,'key-alpha').hex()==payload,'owned payload differs')
        objects.append(raw)
    def observation(raw,key):
        try:return {'kind':'payload','value':tool.extract(raw,key,bypass=bypass).hex()}
        except tool.Rejected as error:return {'kind':'rejection','value':error.kind}
    source=objects[0]
    follow=source
    if relation in {'MR09','MR10'}:
        changed=bytearray(source);start,end=tool.record_bounds(source)
        if relation=='MR09':changed[start:start+4]=b'XXXX'
        else:
            if mode in {'checksum','both','outside','restore'}:changed[end-1]^=1
            if mode in {'payload','both'}:changed[start+15]^=1
            if mode=='outside':changed[-1]^=1
        follow=bytes(changed)
    if relation=='MR02': sequence=[]
    elif relation=='MR04':sequence=[(source,'key-alpha'),(source,'key-beta')]
    elif relation in {'MR05','MR14'}:sequence=[(objects[0],'key-alpha'),(objects[1],'key-alpha')]
    elif relation=='MR13':sequence=[(objects[i],'key-alpha') for i in (0,1,0)]
    elif relation in {'MR08','MR09','MR10'}:
        sequence=[(source,'key-alpha')]
        if shape[1]==2:sequence.append((source if mode=='restore' else follow,'key-alpha'))
    else:sequence=[(source,'key-alpha')]
    for captured,(raw,key) in zip(row['extractions'],sequence):
        require(captured=={'artifact_sha256':hashlib.sha256(raw).hexdigest(), 'key':key,
                           'observation':observation(raw,key)}, 'owned extraction record differs')
    observed=[x['observation'] for x in row['extractions']]
    expected_facts={'subject_exists':True,'isolated_workspace':True}
    expected_obs={}
    if relation=='MR01':expected_obs={'extraction':observed[0]}
    elif relation=='MR02':
        expected_facts['both_hosts_terminate']=True;expected_obs={'mismatches':[]}
    elif relation=='MR03':
        expected_facts['carrier_absent']=True;expected_obs={'carrier':observed[0],'extraction':observed[0]}
    elif relation=='MR04':
        expected_facts.update(source_payload_recovered=True,keys_distinct=True)
        expected_obs={'source':observed[0],'followup':observed[1]}
    elif relation=='MR05':
        expected_obs={'first':observed[0],'second':observed[1],
                      'execution_order':'sequential-builds-then-extract'}
    elif relation=='MR08':
        expected_facts.update(source_payload_recovered=True,artifact_bytes_preserved=True,
                              only_artifact_relocated=True,relocated_host_terminates=True)
        expected_obs={'source':observed[0],'followup':observed[1],'host_outputs_agree':True}
    elif relation in {'MR09','MR10'}:
        expected_facts.update(source_payload_recovered=True,source_carrier_valid=True)
        expected_obs={'source':observed[0],'source_carrier':observed[0]}
        if relation=='MR09':
            expected_facts['carrier_removed']=True
            expected_obs.update(followup_carrier=observed[1],followup=observed[1])
        else:
            expected_facts['source_snapshot_matches_request']=True
            identity=lambda raw:{'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
            snapshots={'source':identity(source)}
            expected_obs['integrity_snapshots']=snapshots
            # Bind the historical string observer to its exact retained
            # carrier slice even when the negative control damages ELF layout.
            # This is parsing bytes, not executing the old permissive parser.
            try:strict={'kind':'payload','value':tool.decode(follow[start:end],'key-alpha').hex()}
            except tool.Rejected as error:strict={'kind':'rejection','value':error.kind}
            expected_obs['followup_carrier']=strict
            expected_facts['integrity_corruption_established']=mode!='none'
            if mode!='none':
                snapshots['followup']=identity(follow)
                locality={'nonintervened_payload_preserved':mode not in {'payload','both'},
                          'checksum_material_changed':mode!='payload',
                          'nonchecksum_material_preserved':mode not in {'payload','both','outside'}}
                expected_obs['integrity_intervention']=locality
                for name,value in locality.items():
                    expected_facts[name]=value
                    if not value:break
                if all(locality.values()):
                    expected_facts.update(followup_snapshot_current=True,
                                          followup_unchanged_during_extraction=mode!='restore')
                    expected_obs['followup']=observed[1]
    elif relation=='MR13':expected_obs=dict(zip(('before','intervening','after'),observed))
    elif relation=='MR14':expected_obs=dict(zip(('before','after'),observed))
    require(facts==expected_facts and row['observations']==expected_obs,
            'owned admission/observation evidence differs from recorded bytes/actions')
    call_objects=objects if relation=='MR02' else [source,source] if relation=='MR08' else []
    expected_calls=[(raw,x) for raw in call_objects for x in INPUTS]
    differences=0
    for call,(raw,value) in zip(row['host_calls'],expected_calls):
        require(type(call['input']) is int and call['input']==value
                and type(call['native']) is int and 0<=call['native']<=tool.MASK
                and call['artifact_sha256']==hashlib.sha256(raw).hexdigest(), 'owned host-call binding differs')
        differences+=call['native']!=tool.expected(family,variant,value)
    require(type(row['host_reference_differences']) is int
            and row['host_reference_differences']==differences==0, 'owned reference difference count contradicts calls')
    direct=expected_verdict if relation=='MR10' else None
    require(row['direct_integrity_verdict']==direct, 'owned direct verdict differs')
    require(type(row['direct_projection_seconds']) in (int,float)
            and math.isfinite(row['direct_projection_seconds']) and row['direct_projection_seconds']>=0,
            'invalid direct projection time')
    return differences

def summarize(rows):
    cohorts={name:Counter() for name in ('clean-workflow','integrity-challenge')}
    result=dict(rows=len(rows),emitted_objects=0,emitted_object_bytes=0,native_calls=0,
                host_reference_differences=0,direct_integrity_disagreements=0,
                case_wall_sum=0.0,case_cpu_sum=0.0)
    verdicts=Counter()
    for row in rows:
        validate_row(row)
        cohort=row['identity'][3];verdict=row['verdict']
        require(cohort in cohorts and verdict in VERDICTS,'unknown owned cohort/verdict')
        cohorts[cohort][verdict]+=1;verdicts[verdict]+=1
        result['emitted_objects']+=len(row['builds'])
        result['emitted_object_bytes']+=sum(len(bytes.fromhex(build['object_hex'])) for build in row['builds'])
        result['native_calls']+=len(row['host_calls'])+sum(len(build['native_inputs']) for build in row['builds'])
        differences=row['host_reference_differences']
        require(type(differences) is int and differences>=0,'invalid reference difference count')
        result['host_reference_differences']+=differences
        if row['direct_integrity_verdict'] is not None:
            require(row['direct_integrity_verdict'] in VERDICTS,'invalid direct verdict')
            result['direct_integrity_disagreements']+=verdict!=row['direct_integrity_verdict']
        for field,target in [('case_seconds','case_wall_sum'),('case_cpu_seconds','case_cpu_sum')]:
            value=row[field]
            require(type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid case time')
            result[target]+=value
    result['verdicts']=dict(verdicts)
    result['cohorts']={name:dict(counts) for name,counts in cohorts.items()}
    return result

def validate_summary(rows,summary):
    require(type(summary['small']) is bool,'small flag must be Boolean')
    expected=[]
    for family in tool.FAMILIES[:1] if summary['small'] else tool.FAMILIES:
        for variant in range(1 if summary['small'] else 4):
            for profile in tool.PROFILES:
                expected.extend([family,variant,profile,'clean-workflow',r,'checksum',False] for r in SHAPES)
                expected.extend([family,variant,profile,'integrity-challenge','MR10',mode,bypass]
                                for mode in ('checksum','none','payload','both','outside','restore')
                                for bypass in (False,True))
    require([row['identity'] for row in rows]==expected,'owned identity plan differs')
    computed=summarize(rows)
    for name,value in computed.items():
        observed=summary[name]
        if name in ('case_wall_sum','case_cpu_sum'):
            require(type(observed) in (int,float) and math.isfinite(observed)
                    and math.isclose(observed,value,rel_tol=1e-12,abs_tol=1e-12),
                    'owned summary/raw mismatch: '+name)
        elif type(value) is int:
            require(type(observed) is int and observed==value,'owned summary/raw mismatch: '+name)
        else:
            require(observed==value,'owned summary/raw mismatch: '+name)
    activity=summary['activity_wall_seconds']
    require(type(activity) in (int,float) and math.isfinite(activity) and activity>=0,
            'invalid outer activity time')
    return computed
