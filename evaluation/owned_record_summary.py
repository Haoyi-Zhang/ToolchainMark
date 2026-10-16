"""Reconstruct owned-object scientific aggregates from retained raw rows.

Standard library only: this module never compiles, loads or executes an object.
"""
from collections import Counter
import math

VERDICTS={'SATISFIED','INCONSISTENT','INADMISSIBLE'}

def require(condition,message):
    if not condition:raise ValueError(message)

def summarize(rows):
    cohorts={name:Counter() for name in ('clean-workflow','integrity-challenge')}
    result=dict(rows=len(rows),emitted_objects=0,emitted_object_bytes=0,native_calls=0,
                host_reference_differences=0,direct_integrity_disagreements=0,
                case_wall_sum=0.0,case_cpu_sum=0.0)
    verdicts=Counter()
    for row in rows:
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
